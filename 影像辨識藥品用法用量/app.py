# -*- coding: utf-8 -*-
"""
影像辨識藥品用法用量 (Drug Vision Dosage Analyzer)
整合醫院 HIS 醫令處方表格解析規則、頻次對照表、劑量單位對照表之全本地免 API Key 主程式
"""

import os
import re
import ssl
import json
import base64
import hashlib
import urllib.request
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, Response
from flask_cors import CORS

from vision_engine import (
    analyze_image_locally_without_api,
    parse_ocr_text_to_structured_data,
    get_demo_sample_result,
    get_all_his_dictionaries,
    lookup_drug_in_tfda_db,
    enrich_medication_result,
    LOG_DIR,
    MEDICAL_ABBREVIATIONS,
)

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True


@app.route("/")
def index():
    """首頁：免 API Key 醫院 HIS 處方箋與藥袋影像辨識平台"""
    resp = app.make_response(render_template("index.html"))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.route("/api/abbreviations", methods=["GET"])
def list_abbreviations():
    """取得常見處方箋與藥袋縮寫對照表"""
    return jsonify({
        "ok": True,
        "abbreviations": MEDICAL_ABBREVIATIONS,
    })


@app.route("/api/his_dictionaries", methods=["GET"])
def his_dictionaries_api():
    """取得完整匯入之醫院 HIS 處方表格解析規則、頻次對照表、劑量單位對照表、劑型與途徑表"""
    return jsonify({
        "ok": True,
        "dictionaries": get_all_his_dictionaries(),
    })


@app.route("/api/demo", methods=["POST"])
def run_demo():
    """載入內建示範 HIS 處方箋或藥袋辨識結果"""
    payload = request.get_json(silent=True) or {}
    sample_type = payload.get("sample_type", "his_prescription")
    result = get_demo_sample_result(sample_type)
    return jsonify({"ok": True, "data": result})


@app.route("/api/analyze", methods=["POST"])
def analyze_image():
    """
    接收外部 APP 或網頁傳入之處方箋／藥袋照片（支援 JSON Base64、multipart/form-data 檔案上傳或 Raw Image Bytes），
    自動辨識藥品名稱、天數、每次劑量、單位、頻次、途徑、總量、藥品外觀特寫圖與一日用藥時間表，回傳結構化 JSON。
    """
    try:
        import urllib.parse
        ocr_text = ""
        image_bytes = b""

        if request.content_type and "multipart/form-data" in request.content_type:
            ocr_text = (request.form.get("ocr_text") or "").strip()
            sample_mode = (request.form.get("sample_mode") or "").strip()
            if sample_mode:
                return jsonify({"ok": True, "data": get_demo_sample_result(sample_mode)})
            for field_name in ("image", "file", "photo", "picture"):
                if field_name in request.files:
                    image_bytes = request.files[field_name].read()
                    if image_bytes:
                        break
            if not image_bytes and request.files:
                first_file = next(iter(request.files.values()))
                image_bytes = first_file.read()
        elif request.content_type and request.content_type.startswith("image/"):
            image_bytes = request.get_data()
        else:
            body = request.get_json(silent=True) or {}
            ocr_text = (body.get("ocr_text") or "").strip()
            sample_mode = (body.get("sample_mode") or "").strip()
            if sample_mode:
                return jsonify({"ok": True, "data": get_demo_sample_result(sample_mode)})

            b64_input = (
                body.get("image_base64")
                or body.get("image")
                or body.get("photo")
                or body.get("base64")
                or ""
            )
            if b64_input:
                if "," in b64_input:
                    b64_input = b64_input.split(",", 1)[1]
                image_bytes = base64.b64decode(b64_input)

        if not image_bytes and not ocr_text:
            return jsonify({"ok": False, "error": "請先上傳或拍攝一張處方箋／藥袋照片，或輸入處方文字"}), 400

        result = analyze_image_locally_without_api(image_bytes, ocr_text_from_client=ocr_text)

        # 為每筆藥品自動補上可直接供外部 APP 載入之 HTTPS 去留白特寫藥錠圖片網址 (proxied_image_url)
        host_base = request.host_url.rstrip("/")
        if request.headers.get("X-Forwarded-Proto", "").lower() == "https" and host_base.startswith("http://"):
            host_base = "https://" + host_base[len("http://"):]
        for med in result.get("medications", []):
            app_info = med.get("appearance")
            if isinstance(app_info, dict):
                raw_url = (app_info.get("image_url") or "").strip()
                if raw_url.startswith("https://mcp.fda.gov.tw/"):
                    app_info["proxied_image_url"] = f"{host_base}/api/pill_image?url={urllib.parse.quote(raw_url, safe='')}&v=2"
                elif raw_url:
                    app_info["proxied_image_url"] = raw_url

        return jsonify({"ok": True, "data": result})

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500


@app.route("/api/parse_ocr_text", methods=["POST"])
def parse_ocr_text_api():
    """直接將多行 HIS 醫令處方文字或藥袋文字解析為完整結構化用藥時間表（免 API Key）"""
    body = request.get_json(silent=True) or {}
    raw_text = (body.get("text") or "").strip()
    if not raw_text:
        return jsonify({"ok": False, "error": "請輸入處方箋或藥袋文字"}), 400
    result = parse_ocr_text_to_structured_data(raw_text)
    return jsonify({"ok": True, "data": result})


@app.route("/api/parse_instruction", methods=["POST"])
def parse_raw_instruction():
    """快速解析單行 HIS 醫令處方文字（例如：'Citao-S f.c. tab 10 mg 28 0.50 TAB HS PO 14 TAB'）"""
    body = request.get_json(silent=True) or {}
    raw_text = (body.get("text") or "").strip()
    if not raw_text:
        return jsonify({"ok": False, "error": "請輸入處方或用法用量文字"}), 400

    structured = parse_ocr_text_to_structured_data(raw_text)
    first_med = (structured.get("medications") or [{}])[0]
    return jsonify({
        "ok": True,
        "raw_text": raw_text,
        "parsed": {
            "drug_name": f"{first_med.get('drug_name_zh', '')} ({first_med.get('drug_name_en', '')})",
            "dosage_per_time": first_med.get("dosage_per_time", "每次 1 錠"),
            "frequency_code": first_med.get("frequency_code", "QD"),
            "frequency_text": first_med.get("frequency_text", "每日 1 次"),
            "timing_code": first_med.get("timing_code", "PC"),
            "timing_text": first_med.get("timing_text", "依醫囑"),
            "route": first_med.get("route", "口服 (PO)"),
            "duration_days": first_med.get("duration_days", 28),
            "total_quantity": first_med.get("total_quantity", "-"),
            "math_formula": first_med.get("math_formula", ""),
            "plain_summary": first_med.get("plain_summary", ""),
        }
    })


@app.route("/api/pill_image", methods=["GET"])
def proxy_pill_image():
    """
    食藥署藥品外觀圖片本地快取與智慧去留白放大端點：
    1. 解決瀏覽器直接載入 mcp.fda.gov.tw 時因台灣政府憑證鏈 (GPKI) 或跨網域限制導致圖片破圖問題。
    2. 自動針對食藥署原圖（含大面積 50mm 尺規留白）進行藥錠主體偵測與去留白放大裁切，讓藥錠正反面清晰呈現。
    """
    target_url = (request.args.get("url") or "").strip()
    if not target_url.startswith("https://mcp.fda.gov.tw/"):
        return Response(status=404)

    pills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "pills")
    os.makedirs(pills_dir, exist_ok=True)
    h = hashlib.md5(target_url.encode("utf-8")).hexdigest()[:16]
    cache_path = os.path.join(pills_dir, f"{h}.jpg")

    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 500:
        resp = app.make_response(send_file(cache_path, mimetype="image/jpeg"))
        resp.headers["Cache-Control"] = "no-cache, must-revalidate"
        return resp

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(target_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            raw_bytes = resp.read()
        if len(raw_bytes) > 500:
            from io import BytesIO
            import numpy as np
            from PIL import Image, ImageFilter, ImageEnhance
            img = Image.open(BytesIO(raw_bytes)).convert("RGB")
            w, ht = img.size
            # 自動裁切掉外圍大面積尺規留白，聚焦於尺規內側藥錠主體
            arr = np.array(img, dtype=np.float32)
            x0, x1 = int(w * 0.16), int(w * 0.80)
            y0, y1 = int(ht * 0.25), int(ht * 0.84)
            roi = arr[y0:y1, x0:x1]
            bg_color = np.median(roi.reshape(-1, 3), axis=0)
            diff = np.linalg.norm(roi - bg_color, axis=2)
            sat = np.max(roi, axis=2) - np.min(roi, axis=2)
            lum = np.mean(roi, axis=2)
            score = diff + sat * 1.5
            score[lum < 75] = 0
            mask = score > max(18.0, np.percentile(score, 90))
            ys, xs = np.where(mask)
            if len(xs) > 50:
                px1, px2 = int(np.percentile(xs, 3)), int(np.percentile(xs, 97))
                py1, py2 = int(np.percentile(ys, 3)), int(np.percentile(ys, 97))
                bw, bh = max(60, px2 - px1), max(50, py2 - py1)
                pad_x, pad_y = int(bw * 0.20), int(bh * 0.22)
                img = img.crop((
                    max(0, x0 + px1 - pad_x),
                    max(0, y0 + py1 - pad_y),
                    min(w, x0 + px2 + pad_x),
                    min(ht, y0 + py2 + pad_y),
                ))
            ratio = 520.0 / max(1, img.width)
            img = img.resize((520, int(img.height * ratio)), Image.Resampling.LANCZOS)
            img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=135, threshold=2))
            img = ImageEnhance.Contrast(img).enhance(1.08)
            img.save(cache_path, format="JPEG", quality=92, optimize=True)
            out_resp = app.make_response(send_file(cache_path, mimetype="image/jpeg"))
            out_resp.headers["Cache-Control"] = "no-cache, must-revalidate"
            return out_resp
    except Exception:
        pass
    return Response(status=404)


@app.route("/api/lookup_drug", methods=["POST"])
def lookup_drug_api():
    """查詢內建藥典與衛福部食藥署 TFDA 72,000+ 筆藥證資料庫，供使用者修改或新增藥品時自動帶入中英文藥名、學名、適應症與警語"""
    body = request.get_json(silent=True) or {}
    drug_name = (body.get("drug_name") or "").strip()
    if not drug_name:
        return jsonify({"ok": False, "error": "請輸入欲查詢的藥品名稱（中文、英文商品名或學名）"}), 400
    found = lookup_drug_in_tfda_db(drug_name)
    if not found:
        return jsonify({"ok": False, "error": f"查無『{drug_name}』對應之藥典資料，您仍可直接手動輸入修改。"}), 404
    return jsonify({"ok": True, "drug": found})


@app.route("/api/confirm_prescription", methods=["POST"])
def confirm_prescription_api():
    """
    接收使用者逐一核對與人工修改完成後之處方資料，
    重新執行用藥時間表排程計算與欄位同步，記錄確認時間戳並存檔備查。
    """
    try:
        body = request.get_json(silent=True) or {}
        presc_data = body.get("data") or body
        if not isinstance(presc_data, dict) or "medications" not in presc_data:
            return jsonify({"ok": False, "error": "處方資料格式不正確"}), 400

        confirmed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for med in presc_data.get("medications") or []:
            med["is_verified"] = True
            # 若使用者修改了 frequency_code，清除舊 time_slots 讓 enrich 重新排程
            med.pop("time_slots", None)

        enriched = enrich_medication_result(presc_data)
        enriched["is_user_confirmed"] = True
        enriched["confirmed_at"] = confirmed_at
        enriched["verified_count"] = len(enriched.get("medications") or [])
        enriched["total_count"] = len(enriched.get("medications") or [])

        os.makedirs(LOG_DIR, exist_ok=True)
        confirm_log_path = os.path.join(LOG_DIR, "last_confirmed_prescription.json")
        with open(confirm_log_path, "w", encoding="utf-8") as f:
            json.dump(enriched, f, ensure_ascii=False, indent=2)

        return jsonify({
            "ok": True,
            "confirmed_at": confirmed_at,
            "data": enriched,
        })
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


if __name__ == "__main__":
    import sys
    import threading
    import webbrowser
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    port = int(os.getenv("PORT", 5080))
    url = f"http://127.0.0.1:{port}"
    print("=" * 68)
    print(" [啟動成功] 影像辨識藥品用法用量系統 (含醫院 HIS 處方規則與對照表)")
    print(f" [本機網址] {url}")
    print("=" * 68)
    if os.getenv("AUTO_OPEN_BROWSER", "1") == "1":
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host="0.0.0.0", port=port, debug=False)
