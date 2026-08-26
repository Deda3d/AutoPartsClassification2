import customtkinter as ctk
import tkinter.ttk as ttk
import cv2
import json
import os
from PIL import Image

# Імпорт ізольованих архітектурних модулів проекту
import database as db
import printer
from detector import SorterDetector

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class WarehouseApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        os.makedirs("labels", exist_ok=True)
        self.title("AI Used Auto Parts Sorting & Labeling System")
        self.geometry("1200x750")
        
        # Ініціалізація ШІ-детектора, камери та прапорців стану UI
        self.detector = SorterDetector()
        self.cap = None
        self.is_paused = False
        self.is_locked = False 
        
        self.frame_counter = 0
        self.ai_skip_frames = 3 
        self.current_part_data = None 
        self.preview_win = None

        # Конфігурація інтерфейсу користувача (Grid Layout)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- ЛІВА ПАНЕЛЬ (Sidebar) ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="🤖 AI WAREHOUSE", font=("Arial", 22, "bold"), text_color="#3498DB").pack(pady=(20, 30))
        ctk.CTkLabel(self.sidebar, text="Вибір камери:").pack(pady=(5, 0))
        
        self.cam_dropdown = ctk.CTkOptionMenu(self.sidebar, values=self.find_cameras(), command=self.change_camera)
        self.cam_dropdown.pack(pady=10)

        self.conf_label = ctk.CTkLabel(self.sidebar, text="Поріг впевненості: 0.50")
        self.conf_label.pack(pady=(15, 0))
        
        self.conf_slider = ctk.CTkSlider(self.sidebar, from_=0.1, to=0.9, command=self.update_conf_label)
        self.conf_slider.set(0.5)
        self.conf_slider.pack(pady=10)

        self.auto_save_var = ctk.BooleanVar(value=False)
        self.auto_save_cb = ctk.CTkCheckBox(self.sidebar, text="Авто-запис у БД", variable=self.auto_save_var)
        self.auto_save_cb.pack(pady=(25, 25))

        self.save_btn = ctk.CTkButton(self.sidebar, text="📥 ЗБЕРЕГТИ В БД", fg_color="#27AE60", state="disabled", command=self.save_to_db_manual)
        self.save_btn.pack(pady=5)

        self.print_btn = ctk.CTkButton(self.sidebar, text="🔁 ДРУКУВАТИ ЗНОВУ", fg_color="#D35400", state="disabled", command=self.simulate_brother_printer)
        self.print_btn.pack(pady=5)

        self.history_btn = ctk.CTkButton(self.sidebar, text="📊 ІСТОРІЯ СКЛАДУ", fg_color="#8E44AD", command=self.open_history_window)
        self.history_btn.pack(pady=30)

        self.pause_btn = ctk.CTkButton(self.sidebar, text="⏸ ПАУЗА КАМЕРИ", fg_color="#5D6D7E", command=self.toggle_pause)
        self.pause_btn.pack(pady=10)

        # --- ЦЕНТРАЛЬНА ЗОНА (Video) ---
        self.video_frame = ctk.CTkFrame(self, fg_color="#1E1E1E")
        self.video_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        self.video_display = ctk.CTkLabel(self.video_frame, text="") 
        self.video_display.pack(expand=True, fill="both")

        # --- ПРАВА ПАНЕЛЬ (Data) ---
        self.data_sidebar = ctk.CTkFrame(self, width=300)
        self.data_sidebar.grid(row=0, column=2, sticky="nsew", padx=(0,15), pady=15)

        ctk.CTkLabel(self.data_sidebar, text="📦 ДАНІ ДЕТАЛІ", font=("Arial", 18, "bold")).pack(pady=15)
        
        self.qr_label = ctk.CTkLabel(self.data_sidebar, text="Очікування...", width=200, height=200, fg_color="#2B2B2B", corner_radius=10)
        self.qr_label.pack(pady=10)

        self.info_box = ctk.CTkTextbox(self.data_sidebar, width=260, height=350, font=("Consolas", 14))
        self.info_box.pack(pady=20)
        self.info_box.insert("1.0", "Покладіть деталь на стіл\nдля початку класифікації...")
        self.info_box.configure(state="disabled")

        self.change_camera("0")
        self.update_frame()

    def update_conf_label(self, value):
        self.conf_label.configure(text=f"Поріг впевненості: {value:.2f}")

    def find_cameras(self):
        available_cameras = []
        for i in range(2):
            temp_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if temp_cap.isOpened():
                available_cameras.append(str(i))
                temp_cap.release()
        return available_cameras if available_cameras else ["0"]

    def change_camera(self, choice):
        if self.cap: self.cap.release()
        self.cap = cv2.VideoCapture(int(choice))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_btn.configure(text="▶ ПРОДОВЖИТИ" if self.is_paused else "⏸ ПАУЗА", 
                                 fg_color="#2980B9" if self.is_paused else "#5D6D7E")

    def save_to_db_manual(self):
        if self.current_part_data:
            db.log_to_history(self.current_part_data)
            self.save_btn.configure(state="disabled", text="✅ ЗБЕРЕЖЕНО")
            self.simulate_brother_printer()
            self.print_btn.configure(state="normal", text="🔁 ДРУКУВАТИ ЗНОВУ")

    def simulate_brother_printer(self):
        if not self.current_part_data: return
        label_img = printer.generate_label(self.current_part_data)
        self.show_printer_preview(label_img)

    def show_printer_preview(self, img):
        if self.preview_win is not None and self.preview_win.winfo_exists():
            self.preview_win.destroy()

        self.preview_win = ctk.CTkToplevel(self)
        self.preview_win.title("Brother QL-810W Print Preview")
        self.preview_win.geometry("750x400") 
        self.preview_win.attributes("-topmost", True)

        ctk.CTkLabel(self.preview_win, text="Симуляція термопринтера (Вихідний файл PNG)", text_color="green", font=("Arial", 14)).pack(pady=10)
        
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(700, 300))
        img_label = ctk.CTkLabel(self.preview_win, image=ctk_img, text="")
        img_label.pack(pady=10)
        
        ctk.CTkButton(self.preview_win, text="Закрити прев'ю", command=self.preview_win.destroy).pack(pady=10)

    def reset_ui_state(self):
        self.qr_label.configure(image="", text="Очікування...")
        self.info_box.configure(state="normal")
        self.info_box.delete("1.0", "end")
        self.info_box.insert("1.0", "Покладіть деталь на стіл\nдля початку класифікації...")
        self.info_box.configure(state="disabled")
        self.save_btn.configure(state="disabled", text="📥 ЗБЕРЕГТИ В БД")
        self.print_btn.configure(state="disabled", text="🔁 ДРУКУВАТИ ЗНОВУ") 
        self.current_part_data = None

    def update_frame(self):
        if self.cap and not self.is_paused:
            ret, frame = self.cap.read()
            if ret:
                self.frame_counter += 1
                annotated_frame = frame.copy()
                
                # Обробка кадру ШІ-модулем виконується асинхронно кожен N-й кадр
                if self.frame_counter % self.ai_skip_frames == 0:
                    conf_threshold = self.conf_slider.get()
                    bbox, name, conf = self.detector.process_frame(frame, conf_threshold)
                    
                    if bbox is not None and not self.is_locked:
                        if self.detector.is_stability_threshold_reached():
                            self.is_locked = True
                            self.process_locked_detection(name, conf)
                
                # Отримання поточних результатів детекції з об'єкта детектора для відмальовування UI
                current_bbox = self.detector.last_bbox
                current_name = self.detector.last_name
                current_conf = self.detector.last_conf

                if current_bbox is not None:
                    x1, y1, x2, y2 = map(int, current_bbox)
                    if not self.is_locked:
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                        cv2.putText(annotated_frame, f"ANALYZING: {current_name} ({current_conf:.2f})", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    else:
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                        cv2.putText(annotated_frame, f"LOCKED: {current_name}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                else:
                    if self.detector.is_table_clear() and self.is_locked:
                        self.is_locked = False
                        self.detector.reset_tracking_state()
                        self.reset_ui_state()
                    if not self.is_locked:
                        cv2.putText(annotated_frame, "TABLE CLEAR. WAITING...", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)

                img = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(700, 500))
                self.video_display.configure(image=ctk_img)

        self.after(50, self.update_frame) 

    def process_locked_detection(self, name, conf):
        db_info = db.get_db_info(name)
        if db_info:
            data = {
                "db_id": db.get_next_db_id(),
                "part": db_info[0],
                "weight_kg": db_info[1],
                "target_zone": db_info[2],
                "robot_instruction": db_info[3],
                "conf": round(conf, 2),
                "cat_id": db_info[4],
                "zone_id": db_info[5]
            }
        else:
            data = {"db_id": db.get_next_db_id(), "part": name, "weight_kg": 0.0, "target_zone": "Unknown", "robot_instruction": "Manual", "conf": round(conf, 2), "cat_id": None, "zone_id": "NONE"}

        self.current_part_data = data
        self.info_box.configure(state="normal")
        self.info_box.delete("1.0", "end")
        self.info_box.insert("1.0", json.dumps(data, indent=2, ensure_ascii=False))
        self.info_box.configure(state="disabled")
        
        import qrcode
        qr_pil = qrcode.make(json.dumps(data, ensure_ascii=False)).convert("RGB")
        ctk_qr = ctk.CTkImage(light_image=qr_pil, dark_image=qr_pil, size=(200, 200))
        self.qr_label.configure(image=ctk_qr, text="")
        self.save_btn.configure(state="normal")

        if self.auto_save_var.get():
            self.save_to_db_manual()

    def open_history_window(self):
        history_win = ctk.CTkToplevel(self)
        history_win.title("Історія сортування складу")
        history_win.geometry("750x450")
        history_win.attributes("-topmost", True)

        tree_frame = ctk.CTkFrame(history_win)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("ID", "Date", "Part Class", "Status")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        for col in columns: tree.heading(col, text=col); tree.column(col, anchor="center")
        tree.pack(fill="both", expand=True, side="left")

        rows = db.fetch_history_records()
        for row in rows: tree.insert("", "end", values=row)

if __name__ == "__main__":
    app = WarehouseApp()
    app.mainloop()


    




#Тимчасовий фрагмент коду для профілювання часових характеристик циклу програми
def update_frame(self):
    if self.cap and not self.is_paused:
        ret, frame = self.cap.read()
        if ret:
            start_time = time.perf_counter()
            self.frame_counter += 1
            annotated_frame = frame.copy()
            
            if self.frame_counter % self.ai_skip_frames == 0:
                conf_threshold = self.conf_slider.get()
                bbox, name, conf = self.detector.process_frame(frame, conf_threshold)
                if bbox is not None and not self.is_locked:
                    if self.detector.is_stability_threshold_reached():
                        self.is_locked = True
                        self.process_locked_detection(name, conf)

            end_time = time.perf_counter()
            frame_time_ms = (end_time - start_time) * 1000
            fps = 1000 / frame_time_ms if frame_time_ms > 0 else 0
            print(f"Цикл кадру: {frame_time_ms:.2f} мс | Апаратний потенціал: {fps:.2f} FPS")