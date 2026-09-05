@echo off
setlocal

cd /d "%~dp0"

where docker >nul 2>&1
if errorlevel 1 (
    echo Docker не найден в PATH. Установите и запустите Docker Desktop.
    pause
    exit /b 1
)

docker compose up --build

endlocal
