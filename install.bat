@echo off
setlocal enabledelayedexpansion
echo ========================================
echo   Lemma 一键安装 (Electron)
echo ========================================
echo.

echo [1/4] 检查 Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    echo 下载地址: https://nodejs.org/
    exit /b 1
)
for /f %%v in ('node --version 2^>^&1') do set NODE_VERSION=%%v
echo   找到 Node.js %NODE_VERSION%

echo [2/4] 安装依赖 (npm ci)...
call npm ci
if errorlevel 1 (
    echo [错误] npm ci 失败！
    exit /b 1
)
echo   依赖安装完成

echo [3/4] 类型检查 (npm run typecheck)...
call npm run typecheck
if errorlevel 1 (
    echo [错误] 类型检查失败！
    exit /b 1
)
echo   类型检查通过

echo [4/4] 构建 Electron 应用 (npm run electron:build)...
call npm run electron:build
if errorlevel 1 (
    echo [错误] 构建失败！
    exit /b 1
)
echo   构建完成

echo.
echo ========================================
echo   安装完成！
echo ========================================
