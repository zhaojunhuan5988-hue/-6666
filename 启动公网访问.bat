@echo off
chcp 65001 >nul
echo ========================================
echo  物料出入库系统 - 一键启动
echo ========================================
echo.

:: 启动Flask服务器
echo [1/2] 启动Flask服务器...
start "Flask ERP" cmd /k "cd /d %~dp0 && python app.py"

:: 等待Flask启动
timeout /t 3 /nobreak >nul

:: 启动内网穿透
echo [2/2] 启动内网穿透...
start cmd /k "lt --port 5000"

echo.
echo ========================================
echo  启动完成！
echo  请等待几秒钟后访问生成的网址
echo ========================================
pause
