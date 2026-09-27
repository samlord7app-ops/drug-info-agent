# 💊 衛福部藥品仿單智慧查詢系統與臨床問答智能體 (Drug Info Agent)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0+](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **全本地運行 · 零付費 API 依賴 · 整合衛福部食藥署 (TFDA) 72,000+ 筆藥證資料庫 · 雙軌臨床智慧衛教問答**

---

## 🌟 核心特色 (Key Features)

### 1. 🔍 官方藥證極速智慧搜尋
* **多維度檢索**：支援中文藥名（如：易週糖、吉舒達、伯基）、英文商品名（Trulicity, Keytruda, Bokey）、主成分（Dulaglutide, Pembrolizumab, Aspirin）及衛署/衛部許可證字號搜尋。
* **電子仿單優先導航**：若該藥品具備 TFDA 官方電子仿單，系統直接呈現電子仿單頁面；若無電子仿單則提供官方最新核定本 PDF 下載。
* **外觀與外盒標籤雙軌支援**：支援藥品本體外觀檢視、外觀核定本下載，以及標籤外盒 PDF 匯出。

### 2. 🤖 雙軌臨床智慧問答引擎 (Dual-Track Clinical QA)
針對每一項臨床問題，系統提供**病人版**與**專業版**雙軌獨立解答：
* **💡 精簡版（一般病人看得懂的白話衛教指引）**：
  * 用平易近人的白話直接回答「能不能、要不要、怎麼用」。
  * **嚴格適配真實給藥途徑**：針劑絕不出現「口服吞服」等錯誤詞彙；GLP-1 注射筆、抗癌單株抗體、口服錠劑各具專屬衛教邏輯。
* **📋 專業版（醫療專業人員專屬，預設摺疊、點選展開）**：
  * 精準引述衛生福利部食品藥物管理署官方仿單之章節條文與項次（如【第 3 節 用法用量】、【第 5 節 警語及注意事項】）。
  * 詳列藥理特性、藥物動力學參數與臨床指引依據。

### 3. 🎯 13 大標準臨床決策題庫
系統杜絕 AI 發散幻覺，嚴格收斂並深度優化 13 類核心臨床諮詢：
1. **藥品作用**：官方核准適應症與臨床機轉。
2. **藥品吃法或用法**：標準劑量方案、劑量漸增階梯 (Titration)、注射部位輪替與調配規範。
3. **腎功能不好要調整劑量嗎？**：eGFR / CrCl 各階段調整原則與透析注意事項。
4. **孕婦可以用嗎？**：懷孕分級、動物試驗毒性與致畸胎風險評估。
5. **小孩最小幾歲可以用，要調整劑量嗎？**：小兒核定最低年齡與體重劑量換算。
6. **老人可以用嗎，要調整劑量嗎？**：高齡族群起始劑量與器官機能退化考量。
7. **肝功能不好可以用嗎，要調整劑量嗎？**：Child-Pugh 分級用藥安全性。
8. **IV 相容性與稀釋配伍禁忌為何？**：專用輸注液（NS / D5W）、過濾器規格、避光與禁忌。
9. **跟哪些藥或食物有交互作用？**：CYP450 代謝、食物禁忌與併用風險。
10. **常見副作用（發生率 >10%）有哪些？**：臨床試驗發生率與處理對策。
11. **特殊警語或病人須注意事項**：黑框警告、重大器官毒性與就醫紅旗徵兆。
12. **拔牙或手術前需要停藥嗎？**：
    * **GLP-1 類藥物（易週糖 Trulicity 等）**：完整指出延遲胃排空導致之全身麻醉/深度鎮靜**肺部異物吸入 (Pulmonary Aspiration)** 重大風險，以及術前告知麻醉團隊與超音波評估指引。
    * **SGLT-2 抑制劑（福適佳 Forxiga 等）**：術前 3 天停藥以防範正常血糖性酮酸中毒 (Euglycemic DKA)。
    * **抗血小板與抗凝血劑**：出血與血栓平衡之停藥天數建議。
    * **癌症免疫治療（吉舒達 Keytruda 等）**：半衰期 26 天且不影響常規拔牙，切勿擅自停藥。
13. **忘記服藥如何處理？**：
    * **易週糖 72 小時黃金法則**（距下次 $\ge$ 3 日儘快補打；未滿 3 日跳過；嚴禁雙倍劑量）。
    * 常規口服藥時間中點原則與針劑補行注射時程。

---

## 🏗️ 系統架構 (Architecture)

```text
drug-info-agent/
├── drug_app.py              # Flask 主應用伺服器、TFDA 爬蟲與 API 端點路由
├── clinical_qa_engine.py    # 臨床問答推論引擎、13 類題庫意圖解析與雙軌文字生成
├── templates/
│   └── drug_search.html     # 單頁現代化 UI (Tailwind CSS, Font Awesome, 響應式佈局)
├── start_drug_agent.bat     # Windows 一鍵啟動腳本
├── requirements.txt         # 專案 Python 依賴套件清單
├── .gitignore               # Git 忽略配置
└── README.md                # 專案說明文件
```

---

## 🚀 快速上手 (Quick Start)

### 1. 環境需求
* **作業系統**：Windows / macOS / Linux
* **Python 版本**：Python 3.10 或以上版本

### 2. 安裝步驟
```bash
# 1. 複製專案庫
git clone https://github.com/samlord7app-ops/drug-info-agent.git
cd drug-info-agent

# 2. 建立並啟動虛擬環境 (建議)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. 安裝必要套件
pip install -r requirements.txt
```

### 3. 啟動服務
* **方法 A（Windows 捷徑）**：
  直接雙擊執行目錄下的 `start_drug_agent.bat`。
* **方法 B（命令列啟動）**：
  ```bash
  python drug_app.py
  ```
啟動後，開啟瀏覽器造訪：**[http://127.0.0.1:5050](http://127.0.0.1:5050)**

---

## 📡 主要 API 端點 (API Endpoints)

| 端點 | 方法 | 說明 |
| :--- | :---: | :--- |
| **`/api/drug_insert`** | **GET / POST** | **仿單查詢核心 HTTP API**：接受 `drug_name` 參數，回傳完整官方仿單 JSON |
| `/api/candidates?q={keyword}` | GET | 即時候選藥品清單與建議提示 |
| `/api/search?drug_name={name}` | GET | 檢索藥品資料、外觀圖片、仿單與電子仿單連結 |
| `/api/ask` | POST | 臨床雙軌智慧問答（輸入 `lic_id` 或 `drug_info` 與 `question` / `q_id`） |
| `/api/download?lic={lic_id}` | GET | 下載官方核定仿單 PDF（若有電子仿單則自動跳轉） |
| `/api/download_appearance?lic={lic_id}` | GET | 下載藥品本體外觀標籤 PDF |

---

### 💡 仿單查詢 API 使用說明 (`/api/drug_insert`)

支援 `GET` 與 `POST` 兩種方式傳遞 `drug_name` 參數（亦支援別名 `/api/drug_info` 與 `/api/insert`）：

#### 1. GET 請求範例
```bash
# 查詢易週糖仿單 JSON
curl -X GET "http://127.0.0.1:5050/api/drug_insert?drug_name=trulicity"

# 支援中英文商品名、學名或許可證字號
curl -X GET "http://127.0.0.1:5050/api/drug_insert?drug_name=易週糖"
```

#### 2. POST 請求範例 (JSON Body)
```bash
curl -X POST "http://127.0.0.1:5050/api/drug_insert" \
     -H "Content-Type: application/json" \
     -d '{"drug_name": "keytruda"}'
```

#### 3. Python 呼叫範例
```python
import requests

url = "http://127.0.0.1:5050/api/drug_insert"
response = requests.get(url, params={"drug_name": "trulicity"})
data = response.json()

if data.get("success"):
    print("品名:", data["cname"], "/", data["ename"])
    print("許可證號:", data["license_id"])
    print("電子仿單網址:", data["e_insert_url"])
    print("用法用量:", data["sections"]["dosage"])
    print("警語與注意事項:", data["sections"]["precautions"])
else:
    print("查詢失敗:", data.get("error"))
```

#### 4. JSON 回傳格式
```json
{
  "success": true,
  "query": "trulicity",
  "drug_name": "trulicity",
  "license_id": "衛部菌疫輸字第001200號",
  "cname": "易週糖注射劑4.5公絲/0.5公撮",
  "ename": "TRULICITY injection 4.5 mg/0.5 mL",
  "ingredient": "DULAGLUTIDE",
  "dosage_form": "注射劑",
  "manufacturer": "ELI LILLY AND COMPANY",
  "revision_date": "113/08/13",
  "is_e_insert": true,
  "e_insert_url": "https://mcp.fda.gov.tw/im_detail_1/...",
  "official_detail_url": "https://info.fda.gov.tw/MLMS/...",
  "has_insert_pdf": true,
  "download_insert_pdf_url": "/api/download?lic=衛部菌疫輸字第001200號",
  "appearance_image_url": "https://info.fda.gov.tw/...",
  "has_appearance_pdf": true,
  "download_appearance_pdf_url": "/api/download_appearance?lic=衛部菌疫輸字第001200號",
  "sections": {
    "indications": "適用於...",
    "dosage": "易週糖的建議起始劑量為0.75 mg每週一次...",
    "contraindications": "對本品過敏者禁用...",
    "precautions": "5.1.9 以全身麻醉或深度鎮靜方式進行手術時之吸入(aspiration)風險...",
    "interactions": "...",
    "adverse_effects": "...",
    "storage": "2°C 至 8°C 冷藏...",
    "patient_info": "..."
  },
  "disambiguation_list": []
}
```

---

## ☁️ 雲端發佈指引 (Firebase App Hosting / Cloud Functions / Cloud Run)

本專案已完整配置 **Firebase App Hosting**、**Firebase Functions (Python 2nd Gen)**、**Google Cloud Run** 以及標準容器化環境所需的全部設定檔（`apphosting.yaml`、`Dockerfile`、`Procfile`、`firebase.json`、`main.py`）：

### 🚀 途徑一：Firebase App Hosting（推薦 · 最簡便全自動 CI/CD）
Firebase App Hosting 為 Google 專為 Web 應用打造的最新代管服務，直接與 GitHub 整合，**每次 push 程式碼自動重新建置並發布**：

1. 開啟 [Firebase Console](https://console.firebase.google.com/) 並選擇或建立您的 Firebase 專案。
2. 在左側選單點選 **「App Hosting」**（應用程式代管），點擊 **「開始使用 (Get started)」**。
3. 授權並選取您的 GitHub 專案庫：`samlord7app-ops/drug-info-agent`。
4. 設定部署分支為 `main`，其餘選項保持預設（系統會自動讀取目錄下的 `apphosting.yaml` 與 `Dockerfile`）。
5. 點擊 **「完成並部署」**，等待 2~3 分鐘即完成部署，Firebase 將自動為您配置專屬安全 HTTPS 網址（例如：`https://<your-project-id>.web.app`）！

### ⚡ 途徑二：Firebase CLI / Cloud Functions (2nd Gen)
若習慣使用本機命令列或欲以伺服器無關 (Serverless) 函式執行：
```bash
# 1. 全域安裝 Firebase CLI (需具備 Node.js)
npm install -g firebase-tools

# 2. 登入 Google 帳號
firebase login

# 3. 初始化並連結現有 Firebase 專案
firebase use --add <your-firebase-project-id>

# 4. 一鍵部署至 Cloud Functions 與 Hosting
firebase deploy
```

### 🐳 途徑三：Google Cloud Run (Direct Container Deploy)
亦可透過 Google Cloud CLI 直接一鍵部署至 Cloud Run：
```bash
gcloud run deploy drug-info-agent \
  --source . \
  --region asia-east1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1
```

---

## 🔒 臨床與法律免責聲明 (Clinical Disclaimer)

本系統所呈現之藥品資訊、電子仿單內容及問答建議，均直接萃取自衛生福利部食品藥物管理署 (TFDA) 最新核定之藥品仿單公開資料與臨床共識。
本系統旨在輔助醫療專業人員（醫師、藥師、護理師）快速查閱資料與提供民眾基礎衛教參考，**不可替代醫師之親自診斷或藥師之專業處方調劑諮詢**。實際臨床用藥仍應依據個別病患之病況、檢驗數值與專業醫師處方指示為準。

---

## 📄 授權條款 (License)

本專案採用 [MIT License](LICENSE) 授權釋出。
