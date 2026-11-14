# -*- coding: utf-8 -*-
"""
影像辨識藥品用法用量系統 - 醫院 HIS 處方表格解析規則、頻次對照表、劑量單位對照表與真實影像 OCR 自動化驗證測試
（含 4 筆標準 HIS 處方箋 + 9 筆密集慢性病處方箋影像辨識驗證）
"""

import os
import io
import sys
import base64
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app


def _build_9_drug_his_test_image() -> bytes:
    """建立模擬真實醫院 HIS 9 種藥品密集處方箋截圖（含藍底反白、無附註連續列、小數點劑量、不同單位與頻次）"""
    img = Image.new("RGB", (680, 360), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_path = "C:/Windows/Fonts/mingliu.ttc"
    f_en = ImageFont.truetype(font_path, 14)

    draw.rectangle([0, 0, 680, 22], fill=(235, 240, 235))
    draw.text((10, 4), "全 . . 處方名稱                               天數  劑量 單位 頻次  途徑   總量 單位", fill=(0, 0, 0), font=f_en)

    rows = [
        ("Citao-S f.c. tab 10 mg (G)[跌]", "28  0.50 TAB  HS    PO      14 TAB", False, ["» 老年人潛在性不適當用藥:在老年人可能引起或加重SIADH或低血鈉"]),
        ("Stilnox f.c. tab 10mg (!)[跌]", "28     1 TAB  HS    PO      28 TAB", True, ["» 半顆到一顆"]),
        ("Eurodin(Estazolam) tab 2mg (!)(G)", "28  0.50 TAB  HS    PO      14 TAB", False, ["» 1/4-1/2顆"]),
        ("Ulstop f.c. tab 20mg (G)", "28     1 TAB  QD    PO      28 TAB", False, []),
        ("Norvasc tab 5mg (G)", "28     1 TAB  QD    PO      28 TAB", False, []),
        ("Bokey e.m. cap 100mg (G)", "28     1 CAP  QD    PO      28 CAP", False, []),
        ("Glucophage tab 500mg (G)", "28     1 TAB  BID   PO      56 TAB", False, []),
        ("Lipitor f.c. tab 20mg", "28  0.50 TAB  HS    PO      14 TAB", False, []),
        ("Concor f.c. tab 5mg (G)", "28     1 TAB  QD    PO      28 TAB", False, []),
    ]

    y = 26
    for name, tail, is_blue, subs in rows:
        if is_blue:
            draw.rectangle([15, y - 2, 675, y + 16], fill=(42, 183, 231))
        draw.rectangle([20, y + 2, 31, y + 13], outline=(100, 100, 100))
        draw.text((65, y), name, fill=(0, 0, 0), font=f_en)
        draw.text((365, y), tail, fill=(0, 0, 0), font=f_en)
        y += 20
        for s in subs:
            draw.text((50, y), s, fill=(20, 20, 120), font=f_en)
            y += 18

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def run_tests():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    client = app.test_client()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. 測試首頁渲染與免責宣言／個資提醒
    r_index = client.get("/")
    assert r_index.status_code == 200, f"Index failed: {r_index.status_code}"
    html_text = r_index.get_data(as_text=True)
    assert "免責宣言" in html_text, "Missing disclaimer in index.html"
    assert "雲端 AI" in html_text, "Missing cloud AI notice in index.html"
    assert "請勿上傳個資" in html_text, "Missing privacy warning in index.html"
    assert "openPillCameraModal" in html_text, "Missing openPillCameraModal in index.html"
    assert "triggerPillFileInput" in html_text, "Missing triggerPillFileInput in index.html"
    assert "拍照修改外觀" in html_text, "Missing 拍照修改外觀 button in index.html"

    # 2. 測試完整 HIS 對照表 API (/api/his_dictionaries)
    r_his_dict = client.get("/api/his_dictionaries")
    assert r_his_dict.status_code == 200
    dicts = r_his_dict.get_json()["dictionaries"]
    assert len(dicts["his_table_rules"]) >= 4
    assert "HS" in dicts["frequencies"]
    assert "BIDPC" in dicts["frequencies"]
    assert "TAB" in dicts["dosage_units"]
    assert "CAP" in dicts["dosage_units"]
    assert "PO" in dicts["routes"]

    # 保存使用者最後上傳之真實處方箋 (若存在)
    last_upload_path = os.path.join(base_dir, "logs", "last_upload.png")
    clinic_sample_path = os.path.join(base_dir, "static", "samples", "sample_clinic_dotmatrix.png")
    hiros_sample_path = os.path.join(base_dir, "static", "samples", "sample_hiros_prescription.png")
    zh_clinic_sample_path = os.path.join(base_dir, "static", "samples", "sample_zh_clinic_rx.png")
    saved_user_bytes = None
    if os.path.exists(last_upload_path):
        with open(last_upload_path, "rb") as f:
            saved_user_bytes = f.read()
        if not os.path.exists(zh_clinic_sample_path) and len(saved_user_bytes) > 1000:
            with open(zh_clinic_sample_path, "wb") as f:
                f.write(saved_user_bytes)

    # 3. 測試真實上傳 4 筆處方箋圖片至 /api/analyze
    his_img_path = os.path.join(base_dir, "static", "samples", "sample_his_prescription.png")
    with open(his_img_path, "rb") as f:
        his_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

    r_analyze = client.post("/api/analyze", json={"image_base64": his_b64, "ocr_text": ""})
    assert r_analyze.status_code == 200
    his_data = r_analyze.get_json()["data"]
    meds = his_data["medications"]
    assert len(meds) == 4, f"Expected 4 HIS medications from real OCR, got {len(meds)}"
    assert "替你憂" in meds[0]["drug_name_zh"] or "Citao-S" in meds[0]["drug_name_zh"]
    assert meds[0]["dose_quantity"] == 0.5
    assert "使蒂諾斯" in meds[1]["drug_name_zh"]
    assert meds[1]["doctor_dose_note"] == "半顆到一顆"
    assert "悠樂丁" in meds[2]["drug_name_zh"]
    assert meds[2]["dose_quantity"] == 0.5
    assert meds[2]["doctor_dose_note"] == "1/4-1/2顆"
    assert "悅潰止" in meds[3]["drug_name_zh"] or "Ulstop" in meds[3]["drug_name_zh"]

    # 4. 測試 9 種藥品密集 HIS 處方箋截圖之真實影像 OCR 辨識（驗證 9 種藥品全數辨識，0 遺漏！）
    img_9_bytes = _build_9_drug_his_test_image()
    b64_9 = "data:image/jpeg;base64," + base64.b64encode(img_9_bytes).decode("utf-8")
    r_9 = client.post("/api/analyze", json={"image_base64": b64_9, "ocr_text": ""})
    assert r_9.status_code == 200
    data_9 = r_9.get_json()["data"]
    meds_9 = data_9["medications"]
    print(f"[9種藥品處方箋實測] 成功辨識筆數: {len(meds_9)} / 9")
    for m in meds_9:
        print(f"  #{m['id']}: {m['drug_name_zh']} | {m['dosage_per_time']} | {m['frequency_code']} | {m['total_quantity']}")
    assert len(meds_9) == 9, f"Expected all 9 medications to be recognized, got {len(meds_9)}"

    # 5. 測試容錯解析（當 OCR 漏讀中間的『1』、邊框有『|』、或單位/途徑有誤讀時仍能 100% 辨識）
    noisy_9_lines = "\n".join([
        "[ ] Citao-S f.c. tab 10 mg (G)[跌] 28 0 50 TkB BS P0 ! 4 TAB |",
        "e ¯ Stilnox f.c. tab 10mg (!)[跌] 28 TAB HS PQ 28 TAE",
        "Eurodin(Estazolam) tab 2mg 1 0 28 0.50 TAB H5 PO 14 TAB ]",
        "Ulstop f.c. tab 20mg (G) 28 TAB Q0 PO 28 TAB",
        "Norvasc tab 5mg 28 1 T4B QD PO 28 TAB",
        "Bokey e.m. cap 100mg 28 C4P QD PO 28 CAP",
        "Glucophage tab 500mg 28 1 TAB B1D PO 56 TAB",
        "Lipitor f.c. tab 20mg 28 .50 TAB HS PO 14 TAB",
        "MgO tab 250mg 28 2 TAB T1D PC PO 168 TAB",
    ])
    r_noisy = client.post("/api/parse_ocr_text", json={"text": noisy_9_lines})
    assert r_noisy.status_code == 200
    noisy_meds = r_noisy.get_json()["data"]["medications"]
    assert len(noisy_meds) == 9, f"Expected 9 noisy medications to be parsed, got {len(noisy_meds)}"
    assert noisy_meds[0]["dose_quantity"] == 0.5
    assert noisy_meds[1]["dose_quantity"] == 1
    assert noisy_meds[3]["dose_quantity"] == 1
    assert noisy_meds[5]["dose_quantity"] == 1
    assert noisy_meds[6]["frequency_code"] == "BID"
    assert noisy_meds[7]["dose_quantity"] == 0.5
    assert noisy_meds[8]["frequency_code"] == "TIDPC"

    # 6. 測試基層診所點陣印表機處方箋 (10 列醫令 / 9 種藥品，含 7.00ccx3x 3 與 必要時)
    if os.path.exists(clinic_sample_path):
        with open(clinic_sample_path, "rb") as f:
            clinic_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
        r_clinic = client.post("/api/analyze", json={"image_base64": clinic_b64, "ocr_text": ""})
        assert r_clinic.status_code == 200
        clinic_meds = r_clinic.get_json()["data"]["medications"]
        print(f"[診所點陣處方箋實測] 成功辨識筆數: {len(clinic_meds)} / 10 (涵蓋全部 9 種藥品)")
        for m in clinic_meds:
            print(f"  #{m['id']}: {m['drug_name_zh']} | {m['dosage_per_time']} | {m['frequency_code']} | {m['duration_days']}天 | {m['total_quantity']}")
        assert len(clinic_meds) == 10
        assert clinic_meds[8]["dose_quantity"] == 7
        assert clinic_meds[8]["duration_days"] == 3
        assert clinic_meds[9]["frequency_code"] == "PRN"

    # 6B. 測試 7 天門診處方箋 (Hiros cap 5/120mg + Viartril-S powder for oral + Broen-C EC tab + Rhin tab)
    if os.path.exists(hiros_sample_path):
        with open(hiros_sample_path, "rb") as f:
            hiros_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
        r_hiros = client.post("/api/analyze", json={"image_base64": hiros_b64, "ocr_text": ""})
        assert r_hiros.status_code == 200
        hiros_meds = r_hiros.get_json()["data"]["medications"]
        print(f"[7天門診處方箋實測] 成功辨識筆數: {len(hiros_meds)} / 4")
        for m in hiros_meds:
            print(f"  #{m['id']}: {m['drug_name_zh']} | 劑型:{m['dosage_form']} | {m['dosage_per_time']} | {m['frequency_code']} | {m['duration_days']}天 | {m['total_quantity']}")
        assert len(hiros_meds) == 4
        assert "Hiros" in hiros_meds[0]["drug_name_en"] and "喜洛" in hiros_meds[0]["drug_name_zh"]
        assert hiros_meds[0]["duration_days"] == 7 and "7 顆（膠囊） (CAP)" in hiros_meds[0]["total_quantity"]
        assert "粉劑" in hiros_meds[1]["dosage_form"] and "膠囊" not in hiros_meds[1]["dosage_form"]
        assert hiros_meds[1]["dose_unit_code"] == "PKG" and hiros_meds[1]["duration_days"] == 90 and "90 包 (PKG)" in hiros_meds[1]["total_quantity"]
        assert "Broen-C" in hiros_meds[2]["drug_name_en"] and hiros_meds[2]["duration_days"] == 7 and "21 錠 (TAB)" in hiros_meds[2]["total_quantity"]
        assert "Rhin" in hiros_meds[3]["drug_name_en"] and hiros_meds[3]["duration_days"] == 7 and "28 錠 (TAB)" in hiros_meds[3]["total_quantity"]

    # 6C. 測試中文表頭門診藥單 (項目名稱 | 次劑量 | 頻率 | 天數 | 總量：benproperine, Broen-C, scanol, strocaine, PSE 60-8, inolin, medicon-A, levocetirzine, meptin)
    if os.path.exists(zh_clinic_sample_path):
        with open(zh_clinic_sample_path, "rb") as f:
            zh_rx_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
        r_zh_rx = client.post("/api/analyze", json={"image_base64": zh_rx_b64, "ocr_text": ""})
        assert r_zh_rx.status_code == 200
        zh_rx_meds = r_zh_rx.get_json()["data"]["medications"]
        print(f"[中文表頭門診藥單實測] 成功辨識筆數: {len(zh_rx_meds)} / 9")
        for m in zh_rx_meds:
            print(f"  #{m['id']}: {m['drug_name_zh']} | {m['dosage_per_time']} | {m['frequency_code']} ({m['frequency_text']}) | {m['duration_days']}天 | {m['total_quantity']}")
        assert len(zh_rx_meds) == 9
        assert "咳定平" in zh_rx_meds[0]["drug_name_zh"] and zh_rx_meds[0]["frequency_code"] == "TIDPC" and zh_rx_meds[0]["duration_days"] == 7
        assert "撲炎喜" in zh_rx_meds[1]["drug_name_zh"] and zh_rx_meds[1]["frequency_code"] == "TIDPC"
        assert "賜康諾" in zh_rx_meds[2]["drug_name_zh"] and zh_rx_meds[2]["frequency_code"] == "TIDPC"
        assert "息痛佳音" in zh_rx_meds[3]["drug_name_zh"] and zh_rx_meds[3]["frequency_code"] == "TIDPC"
        assert "克鼻敏" in zh_rx_meds[4]["drug_name_zh"] and zh_rx_meds[4]["dose_quantity"] == 0.5 and "10.5 錠 (TAB)" in zh_rx_meds[4]["total_quantity"]
        assert "益諾靈" in zh_rx_meds[5]["drug_name_zh"] and zh_rx_meds[5]["dose_quantity"] == 0.5 and "10.5 錠 (TAB)" in zh_rx_meds[5]["total_quantity"]
        assert "滅咳康" in zh_rx_meds[6]["drug_name_zh"] and zh_rx_meds[6]["frequency_code"] == "HS" and "7 顆（膠囊） (CAP)" in zh_rx_meds[6]["total_quantity"]
        assert "左敏停" in zh_rx_meds[7]["drug_name_zh"] and zh_rx_meds[7]["frequency_code"] == "HS" and "7 錠 (TAB)" in zh_rx_meds[7]["total_quantity"]
        assert "滅喘淨" in zh_rx_meds[8]["drug_name_zh"] and zh_rx_meds[8]["dose_quantity"] == 0.5 and "3.5 錠 (TAB)" in zh_rx_meds[8]["total_quantity"]

    # 7. 測試藥典查詢 API (/api/lookup_drug) 與逐一核對、修改完成確認 API (/api/confirm_prescription)
    r_lookup = client.post("/api/lookup_drug", json={"drug_name": "Stilnox"})
    assert r_lookup.status_code == 200
    lookup_drug = r_lookup.get_json()["drug"]
    assert "使蒂諾斯" in lookup_drug["drug_name_zh"]
    assert "appearance" in lookup_drug and lookup_drug["appearance"].get("desc"), "Expected drug appearance in lookup_drug"
    assert lookup_drug["appearance"].get("image_url", "").startswith("https://mcp.fda.gov.tw/"), "Expected official TFDA shapeImg URL"

    # 驗證處方辨識結果皆附帶藥品外觀資訊 (appearance)
    for m in meds:
        assert "appearance" in m and m["appearance"].get("desc"), f"Missing appearance for {m['drug_name_zh']}"

    # 驗證 /api/pill_image 能正確回傳實際藥錠照片 (解決瀏覽器對 mcp.fda.gov.tw 憑證/跨網域阻擋問題)
    r_pill_img = client.get("/api/pill_image", query_string={"url": lookup_drug["appearance"]["image_url"]})
    assert r_pill_img.status_code == 200 and len(r_pill_img.data) > 5000, "Expected /api/pill_image to return cached real pill image"

    # 測試搜尋不在 30 筆內建字典但在 6,374 筆食藥署外觀資料庫中的藥品 (如 Diovan / 易安穩)
    r_lookup_tfda = client.post("/api/lookup_drug", json={"drug_name": "Diovan 160mg"})
    assert r_lookup_tfda.status_code == 200
    tfda_drug = r_lookup_tfda.get_json()["drug"]
    assert tfda_drug and "appearance" in tfda_drug, "Expected TFDA DB lookup to include appearance"

    # 模擬使用者修改第 1 筆藥品劑量為 1 錠、頻次改為 BID，並送出最終確認
    modified_data = dict(his_data)
    modified_data["medications"][0]["dose_quantity"] = 1
    modified_data["medications"][0]["frequency_code"] = "BID"
    modified_data["medications"][0]["is_modified"] = True
    r_confirm = client.post("/api/confirm_prescription", json={"data": modified_data})
    assert r_confirm.status_code == 200
    confirmed_resp = r_confirm.get_json()
    assert confirmed_resp["ok"] is True
    assert confirmed_resp["data"]["is_user_confirmed"] is True
    assert confirmed_resp["data"]["verified_count"] == 4
    assert all(m.get("is_verified") is True for m in confirmed_resp["data"]["medications"])
    # 驗證修改為 BID 後，一日用藥時間表早上與晚上皆有排入第 1 筆藥品
    morning_ids = [item["id"] for item in confirmed_resp["data"]["schedule_grid"]["morning"]]
    evening_ids = [item["id"] for item in confirmed_resp["data"]["schedule_grid"]["evening"]]
    assert 1 in morning_ids and 1 in evening_ids

    # 驗證首頁包含逐一核對橫幅、修改表單與完成確認按鈕函式
    r_index = client.get("/")
    html_text = r_index.get_data(as_text=True)
    assert "verificationBanner" in html_text
    assert "confirmAllMedications" in html_text
    assert "saveMedEdit" in html_text
    assert "toggleVerifyMed" in html_text

    if saved_user_bytes:
        with open(last_upload_path, "wb") as f:
            f.write(saved_user_bytes)

    print("ALL OCR, VERIFICATION REMINDER, MODIFICATION & CONFIRMATION TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
