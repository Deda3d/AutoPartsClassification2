import os
import time
from icrawler.builtin import BingImageCrawler

def rename_files(class_dir, prefix):
    if not os.path.exists(class_dir):
        return
    
    print(f"\n=== Переименование файлов в: {class_dir} ===")
    valid_exts = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')
    
    # Получаем список всех файлов
    files = [f for f in os.listdir(class_dir) 
             if f.lower().endswith(valid_exts) and os.path.isfile(os.path.join(class_dir, f))]
    
    # Сортировка по времени создания
    files.sort(key=lambda x: os.path.getmtime(os.path.join(class_dir, x)))
    
    count = 0
    for i, filename in enumerate(files, 1):
        ext = os.path.splitext(filename)[1].lower()
        new_name = f"{prefix}({i}){ext}"
        old_path = os.path.join(class_dir, filename)
        new_path = os.path.join(class_dir, new_name)
        
        try:
            if old_path != new_path:
                if os.path.exists(new_path):
                    os.remove(new_path)
                os.rename(old_path, new_path)
                count += 1
        except:
            continue
                
    print(f"=== Успешно переименовано: {count} файлов ===")

def collect_parts_safe(class_name, queries, count_per_query=100):
    base_dir = 'car_parts_dataset'
    class_dir = os.path.join(base_dir, class_name.replace(" ", "_"))
    
    if not os.path.exists(class_dir):
        os.makedirs(class_dir)

    print(f"=== Сбор данных для: {class_name} ===")

    for query in queries:
        print(f"\n>>> Работаю над: {query}")
        
        # downloader_threads=20 — просто задавим количеством потоков. 
        # Даже если 5-7 "висят", остальные 13 будут качать.
        crawler = BingImageCrawler(
            downloader_threads=20, 
            storage={'root_dir': class_dir}
        )
        
        # Только базовые аргументы, которые не вызывают ошибок
        crawler.crawl(
            keyword=query, 
            max_num=count_per_query,
            filters={'type': 'photo'}
        )

    # Запускаем переименование
    rename_files(class_dir, "AIR_COMPRESSOR")

if __name__ == "__main__":
    # Чтобы получить больше 150 уникальных фото, 
    # нужно использовать максимально разные запросы по конкретным брендам.
    search_queries = [
        # Запросы с акцентом на авторазборки и б/у рынок (отсекаем новые, схемы, компрессоры для шин)
        "used car ac compressor oem -new -tire -inflator -diagram",
        "salvage yard auto ac compressor -new -remanufactured -box",
        "junkyard car air conditioning compressor -new -diagram",
        
        # Запросы с указанием площадок, где люди сами фоткают снятые детали (на столе, на полу)
        "ebay used oem ac compressor car -new -stock",
        "used genuine automotive ac compressor ebay -new",
        
        # Запросы с акцентом на "снятое" и "на запчасти"
        "scrap car ac pump compressor -new -tire",
        "auto dismantling car ac compressor -new -installed",
        "removed original car ac compressor -new -diagram",
        
        # Акцент на внешний вид б/у детали
        "dirty used car ac compressor part -new",
        "second hand automotive ac compressor -new -box",
        
        # Специфичные запросы с марками авто (отлично работают для уникализации фото)
        "used honda civic ac compressor oem -new",
        "salvaged toyota camry ac compressor part -new -diagram"
    ]
    
    try:
        # Ставим по 100 на каждый из 12 запросов = потенциально 1200 фото.
        # Даже с учетом дублей и ошибок, 500+ штук наберется легко.
        collect_parts_safe("air compressor", search_queries, count_per_query=500)
    except KeyboardInterrupt:
        print("\nОстановка пользователем. Переименовываю...")
        rename_files(os.path.join('car_parts_dataset', 'air_compressor'), "AIR_COMPRESSOR")
    except Exception as e:
        print(f"\nОшибка: {e}")
        rename_files(os.path.join('car_parts_dataset', 'air_compressor'), "AIR_COMPRESSOR")