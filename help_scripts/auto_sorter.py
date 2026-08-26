import cv2
import sqlite3
import json
import time
import qrcode
import numpy as np
from ultralytics import YOLO

# --- НАСТРОЙКИ ---
MODEL_PATH = r'runs/detect/train/weights/best.pt'
DB_PATH = 'warehouse.db'
CONF_THRESHOLD = 0.8  # Твоя планка точности
COOLDOWN_TIME = 3     # Пауза в секундах, чтобы не спамить одной и той же деталью

def get_part_data(class_name):
    """Достает инструкции из БД по имени класса"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = '''
        SELECT p.class_name, p.weight_avg, z.zone_name, z.handling_instruction 
        FROM parts_catalog p
        JOIN logistics_zones z ON p.zone_id = z.zone_id
        WHERE p.class_name = ?
    '''
    cursor.execute(query, (class_name,))
    row = cursor.fetchone()
    conn.close()
    return row

def log_to_history(class_name, conf, proc_time):
    """Записывает результат в таблицу истории"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sorting_history (class_name, confidence, processing_time_sec, status)
        VALUES (?, ?, ?, ?)
    ''', (class_name, conf, proc_time, 'SUCCESS'))
    conn.commit()
    conn.close()

def generate_qr_image(data_dict):
    """Создает QR-код из словаря и конвертирует для OpenCV"""
    qr_data = json.dumps(data_dict, ensure_ascii=False)
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    return cv2.cvtColor(np.array(img_qr), cv2.COLOR_RGB2BGR)

def main():
    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(1)
    last_processed_time = 0
    
    print("🚀 Система запущена. Жду деталь...")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # 1. Детекция
        start_process = time.time()
        results = model.predict(frame, conf=CONF_THRESHOLD, device=0, verbose=False)
        
        annotated_frame = results[0].plot()
        current_time = time.time()

        # 2. Логика обработки (если нашли что-то уверенно и прошло время кулдауна)
        if len(results[0].boxes) > 0 and (current_time - last_processed_time > COOLDOWN_TIME):
            box = results[0].boxes[0]
            class_idx = int(box.cls[0])
            class_name = model.names[class_idx]
            confidence = float(box.conf[0])

            # Ищем в базе
            db_data = get_part_data(class_name)
            
            if db_data:
                proc_time = round(time.time() - start_process, 3)
                
                # Формируем JSON-пакет
                json_package = {
                    "type": "PART_PASSPORT",
                    "part": db_data[0],
                    "weight": db_data[1],
                    "zone": db_data[2],
                    "handling": db_data[3],
                    "timestamp": int(current_time)
                }

                # Вывод в консоль (как ты просил)
                print(f"\n📦 ОБНАРУЖЕНО: {class_name}")
                print(f"📄 JSON ПАКЕТ: {json.dumps(json_package, indent=2, ensure_ascii=False)}")
                
                # Сохраняем в БД
                log_to_history(class_name, confidence, proc_time)
                
                # Генерируем QR
                qr_img = generate_qr_image(json_package)
                qr_img = cv2.resize(qr_img, (300, 300))
                
                # Показываем QR в отдельном окне (симуляция печати)
                cv2.imshow("QR Label (To Print)", qr_img)
                
                last_processed_time = current_time
                print(f"✅ Данные добавлены в БД. QR сформирован за {proc_time} сек.")

        # Вывод основного окна
        cv2.imshow("Warehouse Intelligence Console", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()