import sqlite3
import os

def create_database():
    # Назва файлу бази даних
    db_name = "warehouse.db"

    # Встановлюємо з'єднання
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    print("Створення таблиць з урахуванням логістичних параметрів...")

    # 1. Таблиця зон (куди робот везе деталь)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS storage_zones (
            zone_id TEXT PRIMARY KEY,
            description TEXT,
            handling_type TEXT
        )
    ''')

    # 2. Таблиця категорій (Довідник з вагою та зонами)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS part_categories (
            id INTEGER PRIMARY KEY,
            category_name TEXT NOT NULL,
            zone_id TEXT,
            base_weight_kg REAL,
            FOREIGN KEY (zone_id) REFERENCES storage_zones(zone_id)
        )
    ''')

    # 3. Таблиця історії (Журнал фактично оброблених деталей)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT NOT NULL,
            category_id INTEGER,
            confidence REAL,
            zone_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES part_categories(id),
            FOREIGN KEY (zone_id) REFERENCES storage_zones(zone_id)
        )
    ''')

    # Заповнюємо зони
    zones_data = [
        ('ZONE_A', 'Важкі агрегати (двигуни, КПП)', 'Heavy Lift / Floor Pallet'),
        ('ZONE_B', 'Середня механіка (стартери, помпи)', 'Robotic Arm / Medium Shelf'),
        ('ZONE_C', 'Дрібні деталі та датчики (свічки)', 'Precision Picker / Small Bin'),
        ('ZONE_D', 'Шасі та підвіска (пружини, важелі)', 'Conveyor / Suspended'),
        ('ZONE_E', 'Електроніка та оптика (фари, блоки)', 'Anti-static / Fragile Shelf'),
        ('ZONE_F', 'Кузовні та допоміжні елементи (диски)', 'General Storage / Bulk')
    ]
    cursor.executemany('INSERT INTO storage_zones VALUES (?, ?, ?)', zones_data)

    print("Заповнення довідника: 50 категорій + вага + зони...")
    
    # Список: (ID, Назва, Зона, Вага в кг)
    categories = [
        (0, 'AIR COMPRESSOR', 'ZONE_A', 12.5), (1, 'ALTERNATOR', 'ZONE_B', 6.2),
        (2, 'BATTERY', 'ZONE_A', 18.0), (3, 'BRAKE CALIPER', 'ZONE_B', 4.5),
        (4, 'BRAKE PAD', 'ZONE_D', 1.2), (5, 'BRAKE ROTOR', 'ZONE_D', 8.5),
        (6, 'CAMSHAFT', 'ZONE_F', 4.0), (7, 'CARBERATOR', 'ZONE_F', 2.5),
        (8, 'CLUTCH PLATE', 'ZONE_B', 3.8), (9, 'COIL SPRING', 'ZONE_D', 5.5),
        (10, 'CRANKSHAFT', 'ZONE_A', 25.0), (11, 'CYLINDER HEAD', 'ZONE_A', 45.0),
        (12, 'DISTRIBUTOR', 'ZONE_C', 1.5), (13, 'ENGINE BLOCK', 'ZONE_A', 120.0),
        (14, 'ENGINE VALVE', 'ZONE_C', 0.08), (15, 'FUEL INJECTOR', 'ZONE_C', 0.15),
        (16, 'FUSE BOX', 'ZONE_C', 0.6), (17, 'GAS CAP', 'ZONE_C', 0.1),
        (18, 'HEADLIGHTS', 'ZONE_E', 2.8), (19, 'IDLER ARM', 'ZONE_D', 2.0),
        (20, 'IGNITION COIL', 'ZONE_C', 0.4), (21, 'INSTRUMENT CLUSTER', 'ZONE_E', 1.5),
        (22, 'LEAF SPRING', 'ZONE_D', 35.0), (23, 'LOWER CONTROL ARM', 'ZONE_D', 6.0),
        (24, 'MUFFLER', 'ZONE_D', 12.0), (25, 'OIL FILTER', 'ZONE_F', 0.5),
        (26, 'OIL PAN', 'ZONE_B', 4.0), (27, 'OIL PRESSURE SENSOR', 'ZONE_C', 0.05),
        (28, 'OVERFLOW TANK', 'ZONE_F', 1.2), (29, 'OXYGEN SENSOR', 'ZONE_C', 0.12),
        (30, 'PISTON', 'ZONE_F', 0.8), (31, 'PRESSURE PLATE', 'ZONE_B', 7.5),
        (32, 'RADIATOR', 'ZONE_A', 8.0), (33, 'RADIATOR FAN', 'ZONE_B', 2.0),
        (34, 'RADIATOR HOSE', 'ZONE_F', 0.4), (35, 'RADIO', 'ZONE_E', 1.8),
        (36, 'RIM', 'ZONE_F', 10.5), (37, 'SHIFT KNOB', 'ZONE_F', 0.2),
        (38, 'SIDE MIRROR', 'ZONE_E', 1.4), (39, 'SPARK PLUG', 'ZONE_C', 0.06),
        (40, 'SPOILER', 'ZONE_F', 3.5), (41, 'STARTER', 'ZONE_B', 4.5),
        (42, 'TAILLIGHTS', 'ZONE_E', 1.6), (43, 'THERMOSTAT', 'ZONE_C', 0.25),
        (44, 'TORQUE CONVERTER', 'ZONE_A', 15.0), (45, 'TRANSMISSION', 'ZONE_A', 80.0),
        (46, 'VACUUM BRAKE BOOSTER', 'ZONE_B', 4.5), (47, 'VALVE LIFTER', 'ZONE_C', 0.1),
        (48, 'WATER PUMP', 'ZONE_B', 3.2), (49, 'WINDOW REGULATOR', 'ZONE_E', 2.2)
    ]
    
    cursor.executemany('INSERT INTO part_categories VALUES (?, ?, ?, ?)', categories)

    conn.commit()
    conn.close()
    print(f"\nБазу даних успішно оновлено. Додано 50 категорій з ваговими коефіцієнтами.")

if __name__ == "__main__":
    create_database()