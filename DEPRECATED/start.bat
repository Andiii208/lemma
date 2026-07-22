@echo off
echo ========================================
echo   Lemma - 启动
echo ========================================
echo.

set PYTHONPATH=%~dp0backend\src;%~dp0backend\src\lemma

echo [0/3] 清理端口...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr LISTENING') do (
    echo   终止进程 %%a (端口 8765)
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr LISTENING') do (
    echo   终止进程 %%a (端口 5173)
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo   端口已清理

echo.
echo [1/3] 启动后端 (端口 8765)...
cd /d "%~dp0backend"
start "Lemma Backend" cmd /c "set PYTHONPATH=%~dp0backend\src && python -c "import sys; sys.path.insert(0,'src'); import uvicorn; uvicorn.run('lemma.api.server:app',host='127.0.0.1',port=8765)""

echo [2/3] 等待后端就绪...
:wait_loop
timeout /t 1 /nobreak >nul
curl -s http://127.0.0.1:8765/api/health >nul 2>&1
if errorlevel 1 goto wait_loop
echo   后端已就绪!

echo [3/3] 启动前端 (端口 5173)...
cd /d "%~dp0frontend"
start "Lemma Frontend" cmd /c "npx vite"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   启动完成！
echo   前端: http://localhost:5173
echo   后端: http://localhost:8765
echo   API文档: http://localhost:8765/docs
echo.
echo   按任意键启动 Electron 桌面端...
echo ========================================
pause >nul

cd /d "%~dp0frontend"
start "Lemma Electron" cmd /c "npx electron ."
echo   Electron 已启动!
pause
