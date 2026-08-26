import cv2
import os
import random

# Укажи свои папки
IMAGE_DIR = "./images"
LABEL_DIR = "./labels"

# Твои классы
CLASSES = ['AIR COMPRESSOR', 'ALTERNATOR', 'BATTERY', 'BRAKE CALIPER', 'BRAKE PAD', 'BRAKE ROTOR', 'CAMSHAFT', 'CARBERATOR', 'CLUTCH PLATE', 'COIL SPRING', 'CRANKSHAFT', 'CYLINDER HEAD', 'DISTRIBUTOR', 'ENGINE BLOCK', 'ENGINE VALVE', 'FUEL INJECTOR', 'FUSE BOX', 'GAS CAP', 'HEADLIGHTS', 'IDLER ARM', 'IGNITION COIL', 'INSTRUMENT CLUSTER', 'LEAF SPRING', 'LOWER CONTROL ARM', 'MUFFLER', 'OIL FILTER', 'OIL PAN', 'OIL PRESSURE SENSOR', 'OVERFLOW TANK', 'OXYGEN SENSOR', 'PISTON', 'PRESSURE PLATE', 'RADIATOR', 'RADIATOR FAN', 'RADIATOR HOSE', 'RADIO', 'RIM', 'SHIFT KNOB', 'SIDE MIRROR', 'SPARK PLUG', 'SPOILER', 'STARTER', 'TAILLIGHTS', 'THERMOSTAT', 'TORQUE CONVERTER', 'TRANSMISSION', 'VACUUM BRAKE BOOSTER', 'VALVE LIFTER', 'WATER PUMP', 'WINDOW REGULATOR']

# До какого размера растянуть для просмотра
VIEW_SIZE = 800 

def visualize():
    images = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not images:
        print("Картинки не найдены!")
        return
        
    random.shuffle(images)

    for img_name in images:
        img_path = os.path.join(IMAGE_DIR, img_name)
        label_path = os.path.join(LABEL_DIR, os.path.splitext(img_name)[0] + ".txt")

        if not os.path.exists(label_path):
            continue

        image = cv2.imread(img_path)
        # Растягиваем картинку сразу, чтобы всё было крупным
        image = cv2.resize(image, (VIEW_SIZE, VIEW_SIZE))
        
        with open(label_path, "r") as f:
            lines = f.readlines()
            
        print(f"\n--- Файл: {img_name} ---")
        
        for line in lines:
            parts = line.split()
            cls_id = int(parts[0])
            x_c, y_c, nw, nh = map(float, parts[1:])

            # Название детали
            label_text = CLASSES[cls_id]
            print(f"Определено: {label_text}")

            # Координаты для растянутого изображения (VIEW_SIZE)
            x1 = int((x_c - nw/2) * VIEW_SIZE)
            y1 = int((y_c - nh/2) * VIEW_SIZE)
            x2 = int((x_c + nw/2) * VIEW_SIZE)
            y2 = int((y_c + nh/2) * VIEW_SIZE)

            # Рисуем рамку жирнее (толщина 3)
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
            
            # Рисуем фон для текста, чтобы он читался
            cv2.rectangle(image, (x1, y1 - 35), (x1 + 350, y1), (0, 255, 0), -1)
            cv2.putText(image, label_text, (x1 + 5, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        # Показываем результат
        cv2.imshow("Check (Esc - Exit, Any key - Next)", image)
        
        key = cv2.waitKey(0)
        if key == 27: # Esc
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    visualize()