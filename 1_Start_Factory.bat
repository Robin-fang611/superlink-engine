@echo off
setlocal
title SuperLink 智能工厂控制台

REM Detect Python Command
set "PY_CMD=python"
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
)

REM Get Local IP
for /f "delims=" %%i in ('"%PY_CMD%" -c "import socket; print(([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith('127.')][:1] or ['127.0.0.1'])[0])"') do set "IP=%%i"

cls
echo ==============================================================================
echo 🚀 SuperLink 引擎已就绪！
echo ==============================================================================
echo.
echo    本机请访问：      http://localhost:3000
echo    同局域网其他设备： http://%IP%:3000
echo.
echo ==============================================================================
echo [INFO] 正在启动 Web 控制台...
echo.

"%PY_CMD%" -m streamlit run app.py --server.port 3000 --server.address 0.0.0.0 --server.headless true

pause
