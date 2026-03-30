@echo off
chcp 65001 >nul
echo ====================================
echo   會議管理助手 - 首次安裝
echo ====================================
echo.

:: 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 找不到 Python！請先安裝：
    echo    https://www.python.org/downloads/
    echo    安裝時務必勾選「Add Python to PATH」
    echo    裝好後重新執行 setup.bat
    echo.
    pause
    exit /b 1
)

echo ✅ Python 已安裝
echo.

:: 建立虛擬環境
echo 📦 建立虛擬環境...
if not exist "venv" (
    python -m venv venv
)
echo ✅ 虛擬環境已建立
echo.

:: 啟動虛擬環境並安裝套件
echo 📦 安裝 Python 套件...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo.
echo ✅ 套件安裝完成
echo.

:: 檢查 .env
if not exist ".env" (
    echo ⚠️  找不到 .env 設定檔！
    echo    請複製 .env.template 為 .env，並填入你的 API Keys：
    echo    copy .env.template .env
    echo    然後用記事本編輯 .env
    echo.
) else (
    echo ✅ .env 設定檔已存在
)

:: 安裝 ffmpeg（音檔處理必要工具）
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo 📦 安裝 ffmpeg（音檔處理必要工具）...
    winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  winget 安裝 ffmpeg 失敗，嘗試 pip 安裝替代方案...
        call venv\Scripts\activate.bat
        pip install imageio-ffmpeg
        echo ✅ ffmpeg 替代方案已安裝
    ) else (
        echo ✅ ffmpeg 已透過 winget 安裝
        echo    ⚠️ 請重新開啟終端機讓 PATH 生效
    )
) else (
    echo ✅ ffmpeg 已安裝
)

echo.
echo ====================================
echo   安裝完成！請執行 start.bat 啟動
echo ====================================
echo.
pause
