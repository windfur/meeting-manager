@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================
echo  Meeting Manager - Restart
echo ============================
echo.

:: 檢查虛擬環境
if not exist "venv\Scripts\activate.bat" (
    echo ❌ 虛擬環境不存在，請先執行 setup.bat
    pause
    exit /b 1
)

echo [1/3] 停止 Streamlit 進程...
:: 只殺佔用 8501 port 的進程，不影響其他 Python 程式
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8501.*LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
)
timeout /t 2 /nobreak >nul

echo [2/3] 確認 port 8501 已釋放...
netstat -ano | findstr ":8501.*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo   Port 仍被佔用，再次清理...
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8501.*LISTENING"') do (
        taskkill /F /PID %%p >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)
echo   OK - Port 8501 已釋放

echo [3/3] 啟動 Streamlit...
start "Meeting Manager" cmd /k "cd /d "%~dp0" && venv\Scripts\activate.bat && streamlit run app.py"

echo.
echo ✅ 已啟動！瀏覽器將自動開啟 http://localhost:8501
echo    此視窗可關閉。
pause
