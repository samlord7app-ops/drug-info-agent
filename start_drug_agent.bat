@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo 衛福部藥品仿單智慧查詢系統 - 本地極速伺服器啟動中
echo ========================================================

netstat -ano | findstr "LISTENING" | findstr ":5050" >nul
if %errorlevel% neq 0 (
    echo 伺服器啟動中，請稍候約 3~5 秒...
    if exist ".venv\Scripts\python.exe" (
        start "TFDA 藥品仿單伺服器 (Port 5050)" /min ".venv\Scripts\python.exe" "drug_app.py"
    ) else (
        start "TFDA 藥品仿單伺服器 (Port 5050)" /min python "drug_app.py"
    )

    :wait_loop
    timeout /t 1 /nobreak >nul
    netstat -ano | findstr "LISTENING" | findstr ":5050" >nul
    if %errorlevel% neq 0 goto wait_loop
)

echo ✅ 伺服器已成功運行！正在為您開啟瀏覽器...
start http://127.0.0.1:5050/patient
exit /b 0
