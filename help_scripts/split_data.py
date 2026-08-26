import os
import shutil
import random

# Шляхи
IMG_SOURCE = "./images"
LBL_SOURCE = "./labels"
DEST = "./dataset"

def split_dataset():
    # 1. Очищуємо папку dataset, якщо вона була створена з помилками (опціонально)
    if os.path.exists(DEST):
        shutil.rmtree(DEST)

    # Створюємо структуру знову
    for split in ['train', 'val', 'test']:
        os.makedirs(f"{DEST}/{split}/images", exist_ok=True)
        os.makedirs(f"{DEST}/{split}/labels", exist_ok=True)

    # 2. Збираємо список тільки тих імен, для яких Є лейбл
    # Беремо список із папки labels, так як це наш "золотий стандарт"
    valid_names = [os.path.splitext(f)[0] for f in os.listdir(LBL_SOURCE) if f.endswith('.txt')]
    
    print(f"Знайдено размічених об'єктів: {len(valid_names)}")
    random.shuffle(valid_names)

    # Ділимо: 80% - тренування, 10% - валідація, 10% - тест
    train_idx = int(len(valid_names) * 0.8)
    val_idx = int(len(valid_names) * 0.9)

    count_copied = 0

    for i, name in enumerate(valid_names):
        split = 'train' if i < train_idx else 'val' if i < val_idx else 'test'
        
        # Шукаємо відповідну картинку
        found_img = False
        for ext in ['.jpg', '.jpeg', '.png']:
            img_path = os.path.join(IMG_SOURCE, name + ext)
            if os.path.exists(img_path):
                # Копіюємо картинку
                shutil.copy(img_path, f"{DEST}/{split}/images/")
                # Копіюємо лейбл
                shutil.copy(os.path.join(LBL_SOURCE, name + ".txt"), f"{DEST}/{split}/labels/")
                found_img = True
                count_copied += 1
                break
        
        if not found_img:
            print(f"[!] Попередження: Лейбл є, а картинка для {name} не знайдена.")

    print(f"\Успіх! Сформовано датасет із {count_copied} повних пар.")

if __name__ == "__main__":
    split_dataset()