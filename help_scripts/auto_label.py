import sys
import os
import torch
from PIL import Image
from tqdm import tqdm

import transformers
import transformers.dynamic_module_utils
import transformers.utils.import_utils

transformers.dynamic_module_utils.check_imports = lambda x: []
transformers.utils.import_utils.is_flash_attn_2_available = lambda: False

from transformers import AutoProcessor, AutoModelForCausalLM, AutoConfig

# --- НАЛАШТУВАННЯ ШЛЯХІВ ---
IMAGE_DIR = "./images"   
OUTPUT_DIR = "./labels"

CLASSES = [
    'AIR COMPRESSOR', 'ALTERNATOR', 'BATTERY', 'BRAKE CALIPER', 'BRAKE PAD', 
    'BRAKE ROTOR', 'CAMSHAFT', 'CARBERATOR', 'CLUTCH PLATE', 'COIL SPRING', 
    'CRANKSHAFT', 'CYLINDER HEAD', 'DISTRIBUTOR', 'ENGINE BLOCK', 'ENGINE VALVE', 
    'FUEL INJECTOR', 'FUSE BOX', 'GAS CAP', 'HEADLIGHTS', 'IDLER ARM', 
    'IGNITION COIL', 'INSTRUMENT CLUSTER', 'LEAF SPRING', 'LOWER CONTROL ARM', 
    'MUFFLER', 'OIL FILTER', 'OIL PAN', 'OIL PRESSURE SENSOR', 'OVERFLOW TANK', 
    'OXYGEN SENSOR', 'PISTON', 'PRESSURE PLATE', 'RADIATOR', 'RADIATOR FAN', 
    'RADIATOR HOSE', 'RADIO', 'RIM', 'SHIFT KNOB', 'SIDE MIRROR', 'SPARK PLUG', 
    'SPOILER', 'STARTER', 'TAILLIGHTS', 'THERMOSTAT', 'TORQUE CONVERTER', 
    'TRANSMISSION', 'VACUUM BRAKE BOOSTER', 'VALVE LIFTER', 'WATER PUMP', 'WINDOW REGULATOR'
]

# --- ЗАВАНТАЖЕННЯ МОДЕЛІ ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "microsoft/Florence-2-large"

print("Підготовка конфігурації...")
config = AutoConfig.from_pretrained(model_id, trust_remote_code=True)
if not hasattr(config, 'forced_bos_token_id'):
    config.forced_bos_token_id = None

print(f"Завантаження Florence-2-large на {device}...")
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    config=config,
    trust_remote_code=True, 
    torch_dtype=torch.float16,
    attn_implementation="sdpa" 
).to(device).eval()

processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

os.makedirs(OUTPUT_DIR, exist_ok=True)

def label_images():
    all_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not all_files:
        print(f"Помилка!: В папці {IMAGE_DIR} пусто!")
        return

    for img_name in tqdm(all_files, desc="Точна размітка"):
        # 1. ВИЗНАЧАЄМО КЛАС З ІМЕНІ ФАЙЛУ
        current_class_id = None
        current_class_name = None
        
        # Підготовка імені для пошуку (прибираємо дефіси, приводимо до верхнього регістру)
        search_name = img_name.upper().replace('-', ' ')
        
        for idx, cls_name in enumerate(CLASSES):
            if cls_name in search_name:
                current_class_id = idx
                current_class_name = cls_name
                break
        
        if current_class_id is None:
            # Якщо не знайшли прямий вхід, спробуємо пошукати без пробілів
            search_name_no_spaces = search_name.replace(' ', '')
            for idx, cls_name in enumerate(CLASSES):
                if cls_name.replace(' ', '') in search_name_no_spaces:
                    current_class_id = idx
                    current_class_name = cls_name
                    break

        if current_class_id is None:
            # Пропускаємо файл, якщо не змогли зрозуміти, що на ньому
            continue

        img_path = os.path.join(IMAGE_DIR, img_name)
        try:
            image = Image.open(img_path).convert("RGB")
            w, h = image.size

            # 2. Формування промпту та запуск моделі
            # Додаємо "the whole", щоб модель не боксила дрібні деталі
            prompt = f"<CAPTION_TO_PHRASE_GROUNDING> the whole {current_class_name.lower()}"

            inputs = processor(text=prompt, images=image, return_tensors="pt").to(device)
            inputs['pixel_values'] = inputs['pixel_values'].to(torch.float16)

            with torch.no_grad():
                generated_ids = model.generate(
                    input_ids=inputs["input_ids"],
                    pixel_values=inputs["pixel_values"],
                    max_new_tokens=1024,
                    num_beams=3
                )

            generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
            parsed_answer = processor.post_process_generation(
                generated_text, 
                task="<CAPTION_TO_PHRASE_GROUNDING>", 
                image_size=(w, h)
            )

            results = parsed_answer["<CAPTION_TO_PHRASE_GROUNDING>"]
            
            # 3. ОБИРАЄМО НАЙКРАЩУ РАМКУ (Найбільшу, але не на все фото)
            valid_boxes = []
            for label, bbox in zip(results["labels"], results["bboxes"]):
                x1, y1, x2, y2 = bbox
                bw, bh = abs(x2 - x1) / w, abs(y2 - y1) / h
                
                # Ігноруємо рамки, яки займають > 99% площі (помиока фону)
                if bw > 0.99 and bh > 0.99:
                    continue
                # Ігноруємо шум
                if bw < 0.01 or bh < 0.01:
                    continue
                    
                valid_boxes.append({'box': bbox, 'area': bw * bh})

            if valid_boxes:
                # Сортуємо за площею і беремо найбільшу рамку
                best_box = sorted(valid_boxes, key=lambda x: x['area'], reverse=True)[0]['box']
                x1, y1, x2, y2 = best_box
                
                # Конвертація в YOLO формат
                x_center = ((x1 + x2) / 2) / w
                y_center = ((y1 + y2) / 2) / h
                width = abs(x2 - x1) / w
                height = abs(y2 - y1) / h

                label_file = os.path.join(OUTPUT_DIR, os.path.splitext(img_name)[0] + ".txt")
                with open(label_file, "w") as f:
                    f.write(f"{current_class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                        
        except Exception as e:
            pass # Якщо один файл зламався, йдемо далі

if __name__ == "__main__":
    label_images()
    print(f"\nУспіх! Чисті рамки лежать у: {OUTPUT_DIR}")