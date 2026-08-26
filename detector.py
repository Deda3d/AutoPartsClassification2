import cv2
from ultralytics import YOLO

class SorterDetector:
    def __init__(self, model_path='runs/detect/train/weights/best.pt'):
        # Ініціалізація ШІ-ядра та внутрішніх лічильників стабілізації
        try:
            self.model = YOLO(model_path)
            print("Модель YOLO успішно завантажено в обчислювальний модуль.")
        except Exception as e:
            print(f"Помилка ініціалізації ШІ-ядра: {e}")
            self.model = None

        self.current_detect_class = None
        self.detect_frames_count = 0
        self.required_frames = 6 
        self.empty_frames_count = 0
        
        self.last_bbox = None
        self.last_name = None
        self.last_conf = 0.0

    def process_frame(self, frame, conf_threshold):
        # Якщо модель не завантажена, повертаємо порожній результат
        if not self.model:
            return None, None, 0.0

        # Виконання інференсу нейромережі
        results = self.model.predict(frame, conf=conf_threshold, imgsz=320, verbose=False)
        
        if len(results[0].boxes) > 0:
            # Фільтр максимуму впевненості ШІ
            best_box = max(results[0].boxes, key=lambda b: float(b.conf[0]))
            self.last_name = self.model.names[int(best_box.cls[0])]
            self.last_bbox = best_box.xyxy[0].cpu().numpy()
            self.last_conf = float(best_box.conf[0])
            self.empty_frames_count = 0
            
            # Логіка накопичення підтверджень класу (часова фільтрація)
            if self.last_name == self.current_detect_class:
                self.detect_frames_count += 1
            else:
                self.current_detect_class = self.last_name
                self.detect_frames_count = 1
        else:
            self.last_bbox = None
            self.empty_frames_count += 1
            
        return self.last_bbox, self.last_name, self.last_conf

    def is_stability_threshold_reached(self):
        # Перевірка, чи деталь зафіксована неперервно протягом потрібної кількості кадрів
        return self.detect_frames_count >= self.required_frames

    def is_table_clear(self):
        # Перевірка, чи об'єкт зник з робочої зони конвеєра
        return self.empty_frames_count > 5

    def reset_tracking_state(self):
        # Повне скидання логічних тригерів відстеження
        self.current_detect_class = None
        self.detect_frames_count = 0
        self.last_bbox = None