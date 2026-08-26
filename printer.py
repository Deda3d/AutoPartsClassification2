import json
import qrcode
from PIL import Image, ImageDraw, ImageFont

def generate_label(data):
    label_img = Image.new('RGB', (700, 300), color='white')
    draw = ImageDraw.Draw(label_img)
    
    # Генерація матриці QR-коду з JSON-рядка
    qr = qrcode.make(json.dumps(data, ensure_ascii=False)).convert("RGB")
    qr = qr.resize((260, 260))
    label_img.paste(qr, (20, 20)) 
    
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 32)
        font_id = ImageFont.truetype("arialbd.ttf", 26) 
        font_text = ImageFont.truetype("arial.ttf", 20)
    except:
        font_title = font_id = font_text = ImageFont.load_default()

    text_x = 300 
    draw.text((text_x, 25), "ROBOTIC WAREHOUSE", fill="black", font=font_title)
    draw.line((text_x, 65, 680, 65), fill="black", width=3) 
    
    draw.text((text_x, 75), f"DB ID: #{data['db_id']:05d}", fill="black", font=font_id)
    draw.text((text_x, 110), f"PART: {data['part']}", fill="black", font=font_text)
    draw.text((text_x, 145), f"ZONE: {data['zone_id']}", fill="black", font=font_text)
    draw.text((text_x, 180), f"WEIGHT: {data['weight_kg']} kg", fill="black", font=font_text)
    draw.text((text_x, 215), f"ROBOT: {data['robot_instruction']}", fill="black", font=font_text)
    draw.text((text_x, 255), f"CONF: {data['conf']} (AI-Vision Validated)", fill="#27AE60", font=font_text)

    filename = f"labels/label_{data['db_id']:05d}_{data['part'].replace(' ', '_')}.png"
    label_img.save(filename)
    return label_img