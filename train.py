from ultralytics import YOLO
import torch

if __name__ == '__main__':
    # Провіряємо доступність CUDA
    print(f"Використовуємо пристрій: {'GPU' if torch.cuda.is_available() else 'CPU'}")

    # Завантажуємо модель YOLO11 (Medium)
    model = YOLO("yolo11m.pt") 

    # Запуск навчання нейромережі
    model.train(
        data="data.yaml",
        epochs=150,
        imgsz=224,
        batch=64,
        device=0,
        workers=8,
        patience=50,
        
        # Аугментація
        scale=0.9,          
        translate=0.3,      
        degrees=180.0,      
        fliplr=0.5,         
        flipud=0.5,         
        hsv_h=0.015,        
        hsv_s=0.7,          
        hsv_v=0.4,          
        mosaic=1.0,         
        mixup=0.15,         
        erasing=0.4         
    )