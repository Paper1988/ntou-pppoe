@echo off
setlocal

cd /d "%~dp0.."

echo ========================================
echo          NTOU PPPoE Manager
echo ========================================
echo.

where python >nul 2>&1

if errorlevel 1 (
    echo [ERROR] Python was not found in PATH.
    echo.
    echo Please install Python 3.11 or newer,
    echo then try again.
    echo.
    exit /b 1
)

echo [INFO] Starting NTOU PPPoE Manager...
echo.

python -m ntou_pppoe start

set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo [INFO] NTOU PPPoE Manager stopped.
echo [INFO] Exit code: %EXIT_CODE%

exit /b %EXIT_CODE%
