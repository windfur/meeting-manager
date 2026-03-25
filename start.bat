@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 檢查虛擬環境
if not exist "venv\Scripts\activate.bat" (
    echo ❌ 虛擬環境不存在，請先執行 setup.bat
    pause
    exit /b 1
)

:: 檢查 .env
if not exist ".env" (
    echo ❌ 找不到 .env 設定檔！
    echo    請複製 .env.template 為 .env 並填入 API Keys
    pause
    exit /b 1
)

:: 啟動
call venv\Scripts\activate.bat
echo 🎙️ 會議管理助手啟動中...
echo    瀏覽器將自動開啟，如未開啟請手動前往 http://localhost:8501
echo    按 Ctrl+C 可停止
echo.
streamlit run app.py
pause
