import sqlite3
import uuid

def get_next_db_id():
    try:
        with sqlite3.connect('warehouse.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(id) FROM processed_items')
            max_id = cursor.fetchone()[0]
            return (max_id + 1) if max_id else 1
    except Exception:
        return 1

def get_db_info(class_name):
    try:
        with sqlite3.connect('warehouse.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.category_name, p.base_weight_kg, z.description, z.handling_type, p.id, p.zone_id
                FROM part_categories p 
                JOIN storage_zones z ON p.zone_id = z.zone_id 
                WHERE p.category_name = ?
            ''', (class_name,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Помилка БД: {e}")
        return None

def log_to_history(part_data):
    try:
        with sqlite3.connect('warehouse.db') as conn:
            cursor = conn.cursor()
            item_uuid = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO processed_items (uuid, category_id, confidence, zone_id) 
                VALUES (?, ?, ?, ?)
            ''', (item_uuid, part_data['cat_id'], part_data['conf'], part_data['zone_id']))
            conn.commit()
    except Exception as e:
        print(f"Помилка запису історії: {e}")

def fetch_history_records():
    try:
        with sqlite3.connect('warehouse.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.id, p.timestamp, c.category_name, 'Sorted' 
                FROM processed_items p
                JOIN part_categories c ON p.category_id = c.id
                ORDER BY p.id DESC LIMIT 50
            ''')
            return cursor.fetchall()
    except Exception as e:
        print(f"Помилка історії: {e}")
        return []