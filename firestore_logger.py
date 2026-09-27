"""
firestore_logger.py
===================
衛福部藥品仿單智慧查詢系統 - Google Cloud Firestore 查詢自動存檔紀錄模組

【架構設計】
1. 支援多種 Firebase 憑證載入管道（自動適配 Render 雲端環境與本機開發）：
   - 環境變數 FIREBASE_CREDENTIALS_JSON：包含 Service Account 完整 JSON 字串（最推薦 Render / 雲端代管使用，無須上傳金鑰檔案）
   - 環境變數 FIREBASE_CREDENTIALS_PATH 或 GOOGLE_APPLICATION_CREDENTIALS：指向金鑰 JSON 檔案路徑
   - 專案根目錄預設檔案：serviceAccountKey.json 或 firebase_credentials.json
   - Google Cloud Application Default Credentials
2. 優雅降級防護 (Graceful Degradation)：
   - 若尚未配置 Firebase 憑證，系統會自動處於「待命」狀態並記錄提示，絕不中斷前端藥品查詢與臨床問答流程。
3. 非同步/背景非阻塞日誌寫入 (Non-blocking Async Logging)：
   - 採用 ThreadPoolExecutor 背景執行緒發送存檔請求，API 回應速度完全不受資料庫連線延遲影響。
4. 結構化查詢紀錄 Schema (Collection: drug_queries)：
   - 查詢時間 (timestamp, created_at)
   - 藥品名稱 (drug_name, query)
   - 諮詢問題類別 (category, question)
   - 許可證字號 (license_id)
   - 官方中英文藥名 (cname, ename)
   - 答覆內容摘要 (patient_answer_preview)
   - 官方仿單連結 (insert_url, pdf_url)
   - 客戶端來源 (client_ip, user_agent, source)
   - 處理狀態 (status: success / not_found / error)
"""

import os
import json
import logging
import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("firestore_logger")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [Firestore] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# 全域單例變數
_firebase_initialized = False
_firestore_db = None
_init_attempted = False
_init_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="firestore_worker")

# Firestore 集合名稱（預設為 drug_queries，可由環境變數覆寫）
COLLECTION_NAME = os.getenv("FIRESTORE_COLLECTION", "drug_queries")


def get_firestore_client():
    """
    延遲安全初始化 (Lazy Thread-Safe Initialization)
    回傳 Firestore 雲端資料庫客戶端，若尚未設定憑證則回傳 None。
    """
    global _firebase_initialized, _firestore_db, _init_attempted
    with _init_lock:
        if _init_attempted:
            return _firestore_db

        _init_attempted = True

        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
        except ImportError:
            logger.warning("未偵測到 firebase-admin 套件。請確認 requirements.txt 已包含 firebase-admin。")
            return None

        # 若已在其他地方初始化過 App
        if firebase_admin._apps:
            try:
                _firestore_db = firestore.client()
                _firebase_initialized = True
                logger.info("成功連接至既有 Firebase Admin 應用程式與 Firestore。")
                return _firestore_db
            except Exception as e:
                logger.error(f"獲取既有 Firestore 客戶端失敗：{e}")
                return None

        cred = None

        # 1. 優先檢查環境變數中的完整 JSON 憑證內容（最適合 Render.com / 雲端 PaaS 部署）
        cred_json_env = os.getenv("FIREBASE_CREDENTIALS_JSON") or os.getenv("FIREBASE_SERVICE_ACCOUNT")
        if cred_json_env:
            try:
                cred_dict = json.loads(cred_json_env)
                cred = credentials.Certificate(cred_dict)
                logger.info("已成功自環境變數 FIREBASE_CREDENTIALS_JSON 載入 Firebase 憑證。")
            except Exception as e:
                logger.error(f"解析 FIREBASE_CREDENTIALS_JSON 環境變數時發生錯誤：{e}")

        # 2. 檢查指定檔案路徑
        if not cred:
            cred_path_env = os.getenv("FIREBASE_CREDENTIALS_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path_env and os.path.exists(cred_path_env):
                try:
                    cred = credentials.Certificate(cred_path_env)
                    logger.info(f"已成功自路徑 {cred_path_env} 載入 Firebase 憑證。")
                except Exception as e:
                    logger.error(f"自檔案路徑 {cred_path_env} 載入 Firebase 憑證失敗：{e}")

        # 3. 檢查專案根目錄常見預設金鑰檔案名稱
        if not cred:
            default_key_names = [
                "serviceAccountKey.json",
                "firebase_credentials.json",
                "firebase-key.json",
                "firebase_key.json"
            ]
            for fname in default_key_names:
                candidate_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
                if os.path.exists(candidate_path):
                    try:
                        cred = credentials.Certificate(candidate_path)
                        logger.info(f"已成功於專案目錄載入金鑰檔案：{fname}")
                        break
                    except Exception as e:
                        logger.error(f"讀取金鑰檔案 {fname} 失敗：{e}")

        # 4. 若有明確指定使用 Google Cloud 預設環境憑證 (ADC)
        if not cred and (os.getenv("FIREBASE_USE_ADC") == "1" or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")):
            try:
                cred = credentials.ApplicationDefault()
                logger.info("嘗試使用 ApplicationDefaultCredentials 進行 Firebase 初始化。")
            except Exception as e:
                logger.warning(f"使用 ApplicationDefaultCredentials 失敗：{e}")
                cred = None

        # 若皆未找到有效憑證，進入安全待命模式
        if not cred:
            logger.info("💡 [待命] 尚未檢測到 Firebase Service Account 金鑰設定。Firestore 自動存檔功能暫處於待命狀態（不影響主查詢服務）。")
            return None

        try:
            firebase_admin.initialize_app(cred)
            _firestore_db = firestore.client()
            _firebase_initialized = True
            logger.info(f"✅ Firebase Admin 與 Firestore 初始化成功！自動存檔集合：'{COLLECTION_NAME}'")
            return _firestore_db
        except Exception as e:
            logger.error(f"初始化 Firebase 應用程式失敗：{e}")
            _firestore_db = None
            return None


def is_firestore_enabled() -> bool:
    """檢查 Firestore 是否已啟用並準備就緒"""
    return get_firestore_client() is not None


def _write_record_task(doc_data: dict):
    """背景執行緒真正執行寫入 Firestore 的任務函數"""
    try:
        db = get_firestore_client()
        if not db:
            return

        try:
            from firebase_admin import firestore
            # 優先使用 Firestore 伺服器時間，確保跨時區一致性
            doc_data["server_timestamp"] = firestore.SERVER_TIMESTAMP
        except Exception:
            pass

        # 寫入指定的 Firestore Collection (如 drug_queries)
        col_ref = db.collection(COLLECTION_NAME)
        update_time, doc_ref = col_ref.add(doc_data)
        logger.info(f"✅ [Firestore 存檔成功] 紀錄 ID: {doc_ref.id} | 藥品: {doc_data.get('drug_name')} | 類別: {doc_data.get('category')}")
    except Exception as e:
        logger.error(f"⚠️ [Firestore 存檔異常] 寫入紀錄失敗：{e}（主查詢正常回應）")


def log_query_to_firestore(
    drug_name: str,
    category: str = "",
    result_data: dict = None,
    client_ip: str = "",
    user_agent: str = "",
    source: str = "api",
    status: str = "success",
    error_message: str = ""
):
    """
    非阻塞式自動存檔入口函數 (Non-blocking Public Logger)：
    於背景執行緒將藥品查詢紀錄傳送至 Firestore，絕不增加主 API 響應時間。

    參數：
    - drug_name: 使用者查詢之藥名或許可證字號
    - category: 諮詢問題類別（如「10 常見副作用」、「08 IV相容性」）
    - result_data: 系統產出之回覆字典（包含 patient_answer、insert_url、pdf_url、license_id 等）
    - client_ip: 客戶端連線 IP
    - user_agent: 客戶端瀏覽器標記
    - source: 來源介面（'patient_ui' | 'pharmacist_ui' | 'api'）
    - status: 'success' | 'not_found' | 'error'
    - error_message: 錯誤訊息（若有）
    """
    result_data = result_data or {}

    patient_ans = result_data.get("patient_answer") or result_data.get("answer") or ""
    # 擷取適當長度文字預防超大文檔
    preview = patient_ans[:1000] if patient_ans else ""

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_roc = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

    doc_data = {
        "created_at": now_roc,
        "drug_name": str(drug_name).strip(),
        "category": str(category).strip() if category else "仿單全面查詢",
        "question": str(result_data.get("question") or category or "").strip(),
        "license_id": result_data.get("license_id") or "",
        "cname": result_data.get("cname") or "",
        "ename": result_data.get("ename") or "",
        "dosage_form": result_data.get("dosage_form") or "",
        "manufacturer": result_data.get("manufacturer") or "",
        "insert_url": result_data.get("insert_url") or result_data.get("package_insert_url") or "",
        "pdf_url": result_data.get("pdf_url") or "",
        "patient_answer_preview": preview,
        "source": source,
        "status": status,
        "client_ip": client_ip,
        "user_agent": user_agent[:250] if user_agent else "",
        "error_message": error_message
    }

    # 派發至背景執行緒池非同步執行，完全不阻礙當前請求
    _executor.submit(_write_record_task, doc_data)
