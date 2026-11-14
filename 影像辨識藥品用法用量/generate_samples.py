# -*- coding: utf-8 -*-
"""
產生高擬真台灣醫院「藥袋」與「門診處方箋」測試範例影像
供使用者直接上傳至 Gemini / OpenAI Vision API 進行真實影像辨識測試。
"""

import os
from PIL import Image, ImageDraw, ImageFont


def get_cjk_font(size: int, bold: bool = False):
    """載入 Windows 系統中文字型（微軟正黑體），若無則退回預設字型"""
    candidates = [
        r"C:\Windows\Fonts\msjhbd.ttc" if bold else r"C:\Windows\Fonts\msjh.ttc",
        r"C:\Windows\Fonts\msjh.ttc",
        r"C:\Windows\Fonts\kaiu.ttf",
        r"C:\Windows\Fonts\mingliu.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def create_sample_drug_bag(output_path: str):
    """繪製一張台灣醫院標準藥袋測試圖"""
    img = Image.new("RGB", (900, 1100), (252, 251, 247))
    draw = ImageDraw.Draw(img)

    f_title = get_cjk_font(34, bold=True)
    f_sub = get_cjk_font(22, bold=True)
    f_label = get_cjk_font(20, bold=True)
    f_body = get_cjk_font(21, bold=False)
    f_large = get_cjk_font(28, bold=True)
    f_small = get_cjk_font(17, bold=False)

    # 外框與頂部醫院標頭
    draw.rectangle([25, 25, 875, 1075], outline=(30, 80, 140), width=3)
    draw.rectangle([25, 25, 875, 115], fill=(22, 78, 99))
    draw.text((50, 48), "國立臺灣大學醫學院附設醫院 門診藥袋 (測試樣本)", fill=(255, 255, 255), font=f_title)

    # 病患基本資料區
    draw.rectangle([45, 135, 855, 265], outline=(180, 195, 210), fill=(241, 245, 249), width=2)
    draw.text((65, 150), "病患姓名：陳 ○ 明 (男 / 64歲)", fill=(15, 23, 42), font=f_large)
    draw.text((520, 155), "領藥號：A082941", fill=(185, 28, 28), font=f_large)
    draw.text((65, 205), "看診科別：心臟血管內科", fill=(51, 65, 85), font=f_body)
    draw.text((380, 205), "調劑日期：2026-10-27", fill=(51, 65, 85), font=f_body)
    draw.text((650, 205), "給藥日數：28 天份", fill=(51, 65, 85), font=f_body)

    # 藥品名稱區塊
    draw.rectangle([45, 285, 855, 435], outline=(148, 163, 184), width=2)
    draw.text((65, 300), "【藥品名稱】 脈優錠 5 毫克 (Norvasc Tab 5mg)", fill=(15, 23, 42), font=f_large)
    draw.text((65, 348), "【學名成分】 Amlodipine besylate 5 mg/tab", fill=(71, 85, 105), font=f_body)
    draw.text((65, 388), "【外型特徵】 白色八角形錠劑，一面刻有「PFIZER」，另一面刻有「NVC 5」", fill=(71, 85, 105), font=f_small)

    # 用法用量核心醒目區塊
    draw.rectangle([45, 455, 855, 675], outline=(2, 132, 199), fill=(240, 249, 255), width=3)
    draw.rectangle([45, 455, 855, 505], fill=(2, 132, 199))
    draw.text((65, 467), "★ 用法用量與服藥時間 (Dosage & Administration)", fill=(255, 255, 255), font=f_sub)

    draw.text((70, 525), "服藥頻率：每日一次 (QD) — 早上服用", fill=(12, 74, 110), font=f_large)
    draw.text((70, 575), "服用時間：飯後服用 (PC) — 早餐後 30 分鐘內", fill=(12, 74, 110), font=f_large)
    draw.text((70, 625), "每次用量：每次 1 錠 (口服 PO)        ｜ 總數量：共 28 錠", fill=(185, 28, 28), font=f_large)

    # 適應症、副作用、注意事項
    draw.rectangle([45, 695, 855, 985], outline=(148, 163, 184), width=2)
    draw.text((65, 715), "【臨床用途（適應症）】：高血壓、心絞痛（控制血壓、維持血管暢通）", fill=(21, 128, 61), font=f_label)
    draw.text((65, 770), "【常見副作用】：少數人可能出現足踝水腫、臉部潮紅、輕微頭暈或頭痛。", fill=(180, 83, 9), font=f_label)
    draw.text((65, 825), "【用藥注意事項】：", fill=(185, 28, 28), font=f_label)
    draw.text((85, 862), "1. 服藥期間請避免食用「葡萄柚」或飲用葡萄柚汁，以免影響藥物代謝導致血壓過低。", fill=(30, 41, 59), font=f_body)
    draw.text((85, 900), "2. 請每日固定時間規律服藥，未經醫師同意請勿自行停藥或增減劑量。", fill=(30, 41, 59), font=f_body)
    draw.text((85, 938), "3. 由坐姿或臥姿起身時請放慢動作，避免姿勢性低血壓引起頭暈。", fill=(30, 41, 59), font=f_body)

    draw.text((65, 1015), "調劑藥師：王雅婷 藥師    藥物諮詢專線：(02) 2312-3456 轉 67890", fill=(100, 116, 139), font=f_small)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")


def create_sample_prescription(output_path: str):
    """繪製一張包含 4 種慢性病與症狀用藥的台灣醫院門診處方箋測試圖"""
    img = Image.new("RGB", (1050, 1150), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = get_cjk_font(32, bold=True)
    f_sub = get_cjk_font(22, bold=True)
    f_th = get_cjk_font(19, bold=True)
    f_td = get_cjk_font(18, bold=False)
    f_td_bold = get_cjk_font(19, bold=True)
    f_small = get_cjk_font(16, bold=False)

    # 邊框與標題
    draw.rectangle([20, 20, 1030, 1130], outline=(40, 40, 40), width=3)
    draw.text((310, 40), "平安綜合醫院 門診處方箋 (測試樣本)", fill=(15, 23, 42), font=f_title)
    draw.line([40, 92, 1010, 92], fill=(100, 116, 139), width=2)

    # 病患資訊列
    draw.text((50, 110), "病患姓名：林 ○ 淑芬", fill=(15, 23, 42), font=f_sub)
    draw.text((350, 110), "科別：新陳代謝暨家醫科", fill=(15, 23, 42), font=f_sub)
    draw.text((690, 110), "開立日期：2026-10-27", fill=(15, 23, 42), font=f_sub)
    draw.text((50, 150), "處方編號：RX-20261027-058", fill=(71, 85, 105), font=f_td)
    draw.text((350, 150), "診斷：第二型糖尿病、高膽固醇血症、心血管預防", fill=(71, 85, 105), font=f_td)

    # 表格表頭
    draw.rectangle([40, 195, 1010, 245], fill=(30, 58, 138))
    draw.text((55, 210), "項次 / 藥品名稱 (中英文與規格)", fill=(255, 255, 255), font=f_th)
    draw.text((440, 210), "每次用量", fill=(255, 255, 255), font=f_th)
    draw.text((565, 210), "頻率與服藥時間", fill=(255, 255, 255), font=f_th)
    draw.text((795, 210), "途徑 / 天數 / 總量", fill=(255, 255, 255), font=f_th)

    rows = [
        {
            "name1": "1. 庫魯化錠 500 毫克",
            "name2": "   Glucophage Tab 500mg (Metformin)",
            "dose": "每次 1 錠 (1#)",
            "freq": "BID PC (每日二次 早晚飯後)",
            "total": "口服 PO / 28天 / 共 56 錠",
            "note": "適應症：控制血糖 ｜ 叮嚀：隨餐或飯後立即服用以減輕腸胃不適",
        },
        {
            "name1": "2. 伯基腸溶微粒膠囊 100 毫克",
            "name2": "   Bokey EM Cap 100mg (Aspirin)",
            "dose": "每次 1 顆 (1#)",
            "freq": "QD PC (每日一次 午餐飯後)",
            "total": "口服 PO / 28天 / 共 28 顆",
            "note": "適應症：預防血栓 ｜ 叮嚀：整粒吞服勿咬碎；拔牙或手術前請告知醫師",
        },
        {
            "name1": "3. 立普妥膜衣錠 20 毫克",
            "name2": "   Lipitor F.C. Tab 20mg (Atorvastatin)",
            "dose": "每次 0.5 錠 (半顆)",
            "freq": "HS (每晚睡前一次)",
            "total": "口服 PO / 28天 / 共 14 錠",
            "note": "適應症：降膽固醇 ｜ 叮嚀：每次只吃半顆！禁喝葡萄柚汁，注意有無肌肉痠痛",
        },
        {
            "name1": "4. 普拿疼止痛加強錠 500 毫克",
            "name2": "   Panadol Tab 500mg (Acetaminophen)",
            "dose": "每次 1 錠 (1#)",
            "freq": "PRN Q6H (需要時/每6小時)",
            "total": "口服 PO / 7天 / 共 10 錠",
            "note": "適應症：解熱鎮痛 ｜ 叮嚀：頭痛或發燒時才吃，每日勿超過 8 錠，服藥期間禁酒",
        },
    ]

    y = 255
    for idx, r in enumerate(rows):
        bg = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
        draw.rectangle([40, y, 1010, y + 170], fill=bg, outline=(203, 213, 225), width=1)
        draw.text((55, y + 15), r["name1"], fill=(15, 23, 42), font=f_td_bold)
        draw.text((55, y + 48), r["name2"], fill=(71, 85, 105), font=f_td)
        draw.text((440, y + 28), r["dose"], fill=(185, 28, 28), font=f_td_bold)
        draw.text((565, y + 28), r["freq"], fill=(3, 105, 161), font=f_td_bold)
        draw.text((795, y + 28), r["total"], fill=(15, 23, 42), font=f_td)
        draw.rectangle([55, y + 92, 995, y + 150], fill=(254, 249, 195), outline=(253, 224, 71))
        draw.text((70, y + 110), f"💡 {r['note']}", fill=(113, 63, 18), font=f_small)
        y += 180

    # 底部簽章
    draw.text((50, 1015), "處方醫師簽章：張仁傑 醫師       調劑藥師簽章：陳怡君 藥師", fill=(51, 65, 85), font=f_td_bold)
    draw.text((50, 1060), "※ 領藥時請核對藥袋姓名、藥名與數量，如有用藥疑問請洽藥物諮詢櫃檯。", fill=(100, 116, 139), font=f_small)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    bag_path = os.path.join(base_dir, "static", "samples", "sample_drug_bag.png")
    rx_path = os.path.join(base_dir, "static", "samples", "sample_prescription.png")
    create_sample_drug_bag(bag_path)
    create_sample_prescription(rx_path)
    print("Generated sample images:", bag_path, rx_path)
