@echo off
setlocal
title SuperLink 环境配置向导

echo ==============================================================================
echo                      SuperLink Data Engine 环境初始化
echo ==============================================================================
echo.

REM 1. Check Python
echo [1/3] 正在检查 Python 环境...
set "PY_CMD=python"
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
)

%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未检测到有效的 Python！
    echo 请前往官网下载安装: https://www.python.org/downloads/
    pause
    exit /b
)
echo [OK] 使用命令: %PY_CMD%
echo.

REM 2. Install Dependencies
echo [2/3] 正在安装核心依赖...
"%PY_CMD%" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] 依赖安装失败！请检查网络连接。
    pause
    exit /b
)
echo [OK] 依赖安装完成。
echo.

REM 3. Create .env Template
echo [3/3] 检查配置文件...
if not exist .env (
    echo SERPER_API_KEY=您的Serper_API_Key > .env
    echo ZHIPUAI_API_KEY=您的智谱AI_API_Key >> .env
    echo APP_PASSWORD=admin123 >> .env
    echo USE_PROXY=True >> .env
    echo HTTP_PROXY=http://127.0.0.1:7897 >> .env
    echo # Email Marketing Settings >> .env
    echo SENDER_EMAIL=your_email@example.com >> .env
    echo SENDER_PASSWORD=your_app_password >> .env
    echo SMTP_SERVER=smtp.example.com >> .env
    echo SMTP_PORT=465 >> .env
    echo IMAP_SERVER=imap.example.com >> .env
    echo IMAP_PORT=993 >> .env
    echo [WARN] 已创建 .env 模板，请务必填写 API Key 和邮件设置！
) else (
    echo [OK] .env 配置文件已存在。
)
echo.

echo ==============================================================================
echo                         ✅ 环境配置成功！
echo ==============================================================================
echo 请确保已在 .env 中填写正确的 API Key。
echo 现在，请运行 "1_Start_Factory.bat" 启动系统。
echo.
pause
