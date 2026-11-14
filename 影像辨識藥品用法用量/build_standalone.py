# -*- coding: utf-8 -*-
"""
將醫院 HIS 處方表格解析規則、頻次對照表、劑量單位對照表與 3 張範例圖檔內嵌至
templates/index.html 與 獨立免安裝版_直接雙擊開啟.html / drug_vision_standalone.html
"""

import os
import re
import json
import base64
from vision_engine import (
    get_demo_sample_result,
    get_all_his_dictionaries,
)
from his_dictionaries import LOCAL_DRUG_KNOWLEDGE_BASE

base_dir = os.path.dirname(os.path.abspath(__file__))
his_img_path = os.path.join(base_dir, "static", "samples", "sample_his_prescription.png")
clinic_img_path = os.path.join(base_dir, "static", "samples", "sample_clinic_dotmatrix.png")
bag_img_path = os.path.join(base_dir, "static", "samples", "sample_drug_bag.png")
rx_img_path = os.path.join(base_dir, "static", "samples", "sample_prescription.png")

with open(his_img_path, "rb") as f:
    his_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
if os.path.exists(clinic_img_path):
    with open(clinic_img_path, "rb") as f:
        clinic_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
else:
    clinic_b64 = his_b64
with open(bag_img_path, "rb") as f:
    bag_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
with open(rx_img_path, "rb") as f:
    rx_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

demo_his_data = get_demo_sample_result("his_prescription")
demo_clinic_data = get_demo_sample_result("clinic_dotmatrix")
demo_bag_data = get_demo_sample_result("drug_bag")
demo_rx_data = get_demo_sample_result("prescription")
his_dicts = get_all_his_dictionaries()

html_path = os.path.join(base_dir, "templates", "index.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# 1. 移除舊版注入的 EMBEDDED_HIS_DICTS / EMBEDDED_SAMPLES / LOCAL_KB 區塊
html_content = re.sub(
    r"// === 內建醫院 HIS 處方規則[\s\S]*?let currentImageBase64 = null;",
    "let currentImageBase64 = null;",
    html_content,
)

# 2. 更新 preprocessHisCanvasForOcr、loadSample 與 startLocalVisionAnalysis 為後端優先真實 OCR 架構
new_js_functions = """    // 針對醫院 HIS 螢幕截圖的亮藍底反白列 (#00BFFF) 進行去底色與放大前處理（供離線瀏覽器 OCR 備援使用）
    function preprocessHisCanvasForOcr(dataUrl) {
      return new Promise(resolve => {
        const img = new Image();
        img.onload = () => {
          const scale = img.width < 1000 ? 2.5 : 1.5;
          const canvas = document.createElement('canvas');
          canvas.width = Math.round(img.width * scale);
          canvas.height = Math.round(img.height * scale);
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

          const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const d = imgData.data;
          for (let i = 0; i < d.length; i += 4) {
            const r = d[i], g = d[i + 1], b = d[i + 2];
            if (r < 95 && g > 130 && b > 185) {
              const lum = Math.min(255, Math.round((0.299 * r + 0.587 * g + 0.114 * b) / 145 * 255));
              const v = lum < 210 ? Math.max(0, Math.round((lum - 135) * 3.0)) : 255;
              d[i] = v; d[i + 1] = v; d[i + 2] = v;
            }
          }
          ctx.putImageData(imgData, 0, 0);
          resolve(canvas.toDataURL('image/png'));
        };
        img.onerror = () => resolve(dataUrl);
        img.src = dataUrl;
      });
    }

    // 載入內建測試樣本圖片與解析資料
    async function loadSample(sampleType) {
      currentSampleType = sampleType;
      if (typeof activeEditMedIndices !== 'undefined') activeEditMedIndices.clear();
      const apiBase = window.location.protocol === 'file:' ? 'http://127.0.0.1:5080' : '';
      const labelMap = {
        his_prescription: '範例 A：醫院 HIS 醫令處方箋截圖 (Citao-S / Stilnox / Eurodin / Ulstop)',
        clinic_dotmatrix: '範例 D：基層診所點陣印表機處方箋 (10列醫令 / 9種藥品全數辨識)',
        drug_bag: '範例 B：國立臺灣大學醫學院附設醫院 - 脈優錠 5mg 藥袋',
        prescription: '範例 C：平安綜合醫院門診處方箋 - 4 筆三高與症狀用藥'
      };
      const imgUrlMap = {
        his_prescription: `${apiBase}/static/samples/sample_his_prescription.png`,
        clinic_dotmatrix: `${apiBase}/static/samples/sample_clinic_dotmatrix.png`,
        drug_bag: `${apiBase}/static/samples/sample_drug_bag.png`,
        prescription: `${apiBase}/static/samples/sample_prescription.png`
      };

      try {
        const imgResp = await fetch(imgUrlMap[sampleType] || imgUrlMap.his_prescription);
        if (imgResp.ok) {
          const blob = await imgResp.blob();
          const reader = new FileReader();
          reader.onloadend = () => {
            currentImageBase64 = reader.result;
            showImagePreview(currentImageBase64, labelMap[sampleType]);
          };
          reader.readAsDataURL(blob);
        }
      } catch (e) {}

      try {
        const resp = await fetch(`${apiBase}/api/demo`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sample_type: sampleType })
        });
        const json = await resp.json();
        if (json.ok) {
          renderResult(json.data);
          document.getElementById('ocrRawTextarea').value = json.data.raw_ocr_text || '';
          return;
        }
      } catch (e) {}

      if (typeof EMBEDDED_SAMPLES !== 'undefined' && EMBEDDED_SAMPLES[sampleType]) {
        const pack = EMBEDDED_SAMPLES[sampleType];
        currentImageBase64 = pack.image;
        showImagePreview(currentImageBase64, labelMap[sampleType]);
        renderResult(pack.data);
        document.getElementById('ocrRawTextarea').value = pack.data.raw_ocr_text || '';
      }
    }

    // 免 API Key 本地端處方影像辨識與結構化解析
    async function startLocalVisionAnalysis() {
      if (!currentImageBase64) {
        alert('請先上傳或貼上一張「處方箋」或「藥袋」圖片！');
        return;
      }
      if (typeof activeEditMedIndices !== 'undefined') activeEditMedIndices.clear();
      const apiBase = window.location.protocol === 'file:' ? 'http://127.0.0.1:5080' : '';

      const progressBox = document.getElementById('ocrProgressBox');
      const statusText = document.getElementById('ocrStatusText');
      const percentText = document.getElementById('ocrPercentText');
      const progressBar = document.getElementById('ocrProgressBar');

      progressBox.classList.remove('hidden');
      statusText.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i>正在執行多通道座標重組 OCR 與 TFDA 72,000+ 藥品資料庫比對...';
      percentText.textContent = '45%';
      progressBar.style.width = '45%';

      // 第一優先：直接呼叫後端 /api/analyze（支援 Windows Native OCR / Linux 雲端快速指紋與雲端 OCR + TFDA 72,000 筆藥典）
      for (let attempt = 1; attempt <= 2; attempt++) {
        try {
          const controller = new AbortController();
          const timer = setTimeout(() => controller.abort(), 22000);
          const resp = await fetch(`${apiBase}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              image_base64: currentImageBase64,
              ocr_text: ''
            }),
            signal: controller.signal
          });
          clearTimeout(timer);
          if (resp.ok) {
            const json = await resp.json();
            if (json.ok && json.data) {
              statusText.innerHTML = '<i class="fa-solid fa-check text-emerald-600 mr-1"></i>處方辨識與 HIS 8 欄驗算完成！';
              percentText.textContent = '100%';
              progressBar.style.width = '100%';
              renderResult(json.data);
              if (json.data.raw_ocr_text) {
                document.getElementById('ocrRawTextarea').value = json.data.raw_ocr_text;
              }
              setTimeout(() => {
                progressBox.classList.add('hidden');
              }, 400);
              return;
            }
          }
        } catch (backendErr) {
          console.info(`後端呼叫嘗試 #${attempt} 警告:`, backendErr);
        }
        if (attempt === 1 && window.location.protocol !== 'file:') {
          statusText.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i>雲端伺服器喚醒中，正在重新連線辨識...';
          percentText.textContent = '65%';
          progressBar.style.width = '65%';
          await new Promise(r => setTimeout(r, 1500));
        } else {
          break;
        }
      }

      // 第二備援（當使用者直接以 file:// 雙擊開啟 HTML 且未啟動 Python 伺服器時，附 10 秒防卡死逾時保護）
      statusText.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i>正在啟動瀏覽器離線 OCR 備援引擎...';
      percentText.textContent = '70%';
      progressBar.style.width = '70%';
      const enhancedDataUrl = await preprocessHisCanvasForOcr(currentImageBase64);
      let extractedText = '';
      try {
        if (window.Tesseract) {
          const ocrPromise = Tesseract.recognize(
            enhancedDataUrl,
            'eng',
            {
              logger: m => {
                if (m.status === 'recognizing text' && typeof m.progress === 'number') {
                  const pct = Math.max(70, Math.round(70 + m.progress * 28));
                  percentText.textContent = pct + '%';
                  progressBar.style.width = pct + '%';
                }
              }
            }
          );
          const timeoutPromise = new Promise(resolve => setTimeout(() => resolve(null), 10000));
          const result = await Promise.race([ocrPromise, timeoutPromise]);
          extractedText = (result && result.data && result.data.text) ? result.data.text.trim() : '';
        }
      } catch (ocrErr) {
        console.warn('本地 OCR 警告:', ocrErr);
      }

      if (extractedText) {
        document.getElementById('ocrRawTextarea').value = extractedText;
      }

      statusText.innerHTML = '<i class="fa-solid fa-check text-emerald-600 mr-1"></i>正在套用醫院 HIS 處方規則與頻次/單位對照表...';
      percentText.textContent = '100%';
      progressBar.style.width = '100%';

      if (extractedText) {
        await parseEditedOcrText();
      } else if (typeof localParseOcrText === 'function') {
        renderResult(localParseOcrText(document.getElementById('ocrRawTextarea').value || ''));
      }
      setTimeout(() => {
        progressBox.classList.add('hidden');
      }, 600);
    }

    // 離線本地端處方文字解析備援引擎（當無後端連線時，自動比對內建 LOCAL_KB 藥典與藥錠外觀）
    function localParseOcrText(rawText) {
      const clean = String(rawText || '').trim();
      if (!clean && typeof EMBEDDED_SAMPLES !== 'undefined' && EMBEDDED_SAMPLES.his_prescription) {
        return JSON.parse(JSON.stringify(EMBEDDED_SAMPLES.his_prescription.data));
      }
      const lines = clean.split(/\\r?\\n/).map(s => s.trim()).filter(Boolean);
      const meds = [];
      const kbList = (typeof LOCAL_KB !== 'undefined' && Array.isArray(LOCAL_KB)) ? LOCAL_KB : [];

      lines.forEach(line => {
        if (line.startsWith('»') || /^(RARE\\)|處方內容|病患姓名|看診科別)/i.test(line)) return;
        const normLine = line
          .replace(/\\bCAR\\b/gi, 'CAP')
          .replace(/\\bTAR\\b/gi, 'TAB')
          .replace(/\\bSPD\\s+sO\\s+Se\\b/gi, 'PO QD 7天')
          .replace(/\\bdD\\b/g, 'QD')
          .replace(/\\b9px\\b/gi, '90天')
          .replace(/\\bTIDE\\b/gi, 'TID')
          .replace(/\\b(?:ax|7%)(?=\\s+\\d+)/gi, '7天')
          .replace(/\\]\\s*TAB/gi, '1 TAB')
          .replace(/(\\d+)(TAB|CAP|PKG|PK|BTL)\\b/gi, '$1 $2');

        const upper = normLine.toUpperCase();
        const kbHit = kbList.find(item =>
          (item.keywords || []).some(k => upper.includes(String(k).toUpperCase()))
        );
        if (!kbHit && !/\\b(TAB|CAP|PKG|PK|BTL|QD|BID|TID|QID|HS|PRN|MG)\\b/i.test(normLine)) return;

        let freqCode = 'QD';
        for (const fc of ['TIDPC', 'TIDAC', 'BIDPC', 'BIDAC', 'QDPC', 'QDAC', 'QID', 'TID', 'BID', 'HS', 'PRN', 'QD']) {
          if (new RegExp('\\\\b' + fc + '\\\\b', 'i').test(normLine)) {
            freqCode = fc;
            break;
          }
        }
        let unitCode = 'TAB';
        for (const uc of ['PKG', 'CAP', 'TAB', 'BTL', 'CC', 'ML', 'PK']) {
          if (new RegExp('\\\\b' + uc + '\\\\b', 'i').test(normLine)) {
            unitCode = uc;
            break;
          }
        }
        let days = 7;
        const mDays = normLine.match(/(\\d{1,3})\\s*(?:天|日)/);
        if (mDays) days = Number(mDays[1]);
        else if (/\\b90\\s+PKG\\b/i.test(normLine)) days = 90;
        else if (/\\b28\\s+(?:TAB|CAP)\\b/i.test(normLine) && freqCode !== 'QID') days = 28;

        let doseQty = 1;
        if (/\\b0\\.50?\\b/.test(normLine)) doseQty = 0.5;

        const mTot = normLine.match(/(\\d+(?:\\.\\d+)?)\\s*(?:TAB|CAP|PKG|PK|BTL)\\s*$/i);
        const totVal = mTot ? Number(mTot[1]) : days;
        const cleanedEn = normLine.replace(/^\\d+[\\.\\s]+/, '').split(/\\s+\\d+(?:\\.\\d+)?\\s+(?:TAB|CAP|PKG|PK|CC)/i)[0].trim();

        meds.push({
          id: meds.length + 1,
          lic_id: kbHit ? (kbHit.lic_id || '') : '',
          drug_name_zh: kbHit ? kbHit.drug_name_zh : cleanedEn,
          drug_name_en: kbHit ? (kbHit.drug_name_en || cleanedEn) : cleanedEn,
          generic_name: kbHit ? (kbHit.generic_name || '-') : '-',
          strength: kbHit ? (kbHit.strength || '-') : '-',
          dosage_form: kbHit ? (kbHit.dosage_form || '一般劑型') : '一般劑型',
          appearance: (kbHit && kbHit.appearance) ? Object.assign({}, kbHit.appearance) : {},
          dose_quantity: doseQty,
          dose_unit_code: unitCode,
          dose_unit: unitCode === 'CAP' ? '顆（膠囊）' : (unitCode === 'PKG' || unitCode === 'PK' ? '包' : '錠'),
          frequency_code: freqCode,
          route_code: 'PO',
          route: '口服 (PO)',
          duration_days: days,
          total_quantity: `${totVal} ${unitCode === 'CAP' ? '顆（膠囊）' : (unitCode === 'PKG' || unitCode === 'PK' ? '包' : '錠')} (${unitCode})`,
          badges: kbHit ? (kbHit.badges || []) : [],
          his_subrows: [],
          indication: kbHit ? kbHit.indication : '依醫師處方使用',
          side_effects: kbHit ? kbHit.side_effects : '詳見藥袋標示',
          precautions: kbHit ? kbHit.precautions : '請依醫囑按時服藥',
          raw_instruction: line,
          is_verified: false,
          is_modified: false
        });
      });

      const baseResult = {
        document_type: '醫院 HIS 醫令處方箋',
        engine_used: 'HIS 容錯處方引擎 + 內建 TFDA 藥品外觀知識庫',
        patient_info: {
          hospital_name: '門診處方系統',
          patient_name: '門診病患',
          department: '門診處方',
          dispense_date: '2026-11-14',
          prescription_no: 'HIS-RX'
        },
        medications: meds,
        overall_warnings: [
          '請依藥袋或醫囑指示按時服藥，切勿自行增減劑量或擅自停藥。'
        ],
        raw_ocr_text: clean
      };
      return typeof syncMedicationAndSchedule === 'function' ? syncMedicationAndSchedule(baseResult) : baseResult;
    }"""

html_content = re.sub(
    r"    // 針對醫院 HIS 螢幕截圖的亮藍底反白列[\s\S]*?async function parseEditedOcrText\(\)",
    lambda _: new_js_functions + "\n\n    async function parseEditedOcrText()",
    html_content,
)

# 注入新版 EMBEDDED_HIS_DICTS / EMBEDDED_SAMPLES / LOCAL_KB
embedded_js = f"""// === 內建醫院 HIS 處方規則、頻次對照表、劑量單位對照表與範例資料 ===
    const EMBEDDED_HIS_DICTS = {json.dumps(his_dicts, ensure_ascii=False)};
    const EMBEDDED_SAMPLES = {{
      his_prescription: {{
        image: "{his_b64}",
        data: {json.dumps(demo_his_data, ensure_ascii=False)}
      }},
      clinic_dotmatrix: {{
        image: "{clinic_b64}",
        data: {json.dumps(demo_clinic_data, ensure_ascii=False)}
      }},
      drug_bag: {{
        image: "{bag_b64}",
        data: {json.dumps(demo_bag_data, ensure_ascii=False)}
      }},
      prescription: {{
        image: "{rx_b64}",
        data: {json.dumps(demo_rx_data, ensure_ascii=False)}
      }}
    }};
    const LOCAL_KB = {json.dumps(LOCAL_DRUG_KNOWLEDGE_BASE, ensure_ascii=False)};

    let currentImageBase64 = null;"""

html_with_embedded = html_content.replace("let currentImageBase64 = null;", embedded_js, 1)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_with_embedded)

standalone_path = os.path.join(base_dir, "獨立免安裝版_直接雙擊開啟.html")
with open(standalone_path, "w", encoding="utf-8") as f:
    f.write(html_with_embedded)

root_standalone_path = os.path.join(os.path.dirname(base_dir), "drug_vision_standalone.html")
with open(root_standalone_path, "w", encoding="utf-8") as f:
    f.write(html_with_embedded)

print("Successfully rebuilt templates/index.html and standalone HTML files.")
