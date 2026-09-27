@echo off
chcp 65001 >nul
echo 正在檢查藥品仿單智慧查詢系統...
netstat -ano | findstr "LISTENING" | findstr ":5050" >nul
if %errorlevel% neq 0 (
    echo 伺服器尚未啟動，正在為您啟動本地服務 (Port 5050)...
    if exist "%~dp0.venv\Scripts\python.exe" (
        start "TFDA 藥品仿單伺服器 (Port 5050)" /min "%~dp0.venv\Scripts\python.exe" "%~dp0drug_app.py"
    ) else (
        start "TFDA 藥品仿單伺服器 (Port 5050)" /min python "%~dp0drug_app.py"
    )
    timeout /t 3 /nobreak >nul
) else (
    echo 伺服器已在運行中。
)
echo 正在開啟瀏覽器...
start http://127.0.0.1:5050
exit /b 0
