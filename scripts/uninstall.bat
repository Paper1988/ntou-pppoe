@echo off
setlocal

cd /d "%~dp0.."

set "TASK_NAME=NTOU-PPPoE Manager"

:: Check for administrator privileges
net session >nul 2>&1

if errorlevel 1 (
    echo [INFO] Administrator privileges are required to uninstall the scheduled task.
    echo [INFO] Requesting elevation...
    echo.

    powershell -NoProfile -Command ^
        "Start-Process -FilePath '%~f0' -Verb RunAs"

    exit /b 0
)

echo ========================================
echo          NTOU PPPoE Manager
echo             Uninstallation
echo ========================================
echo.

echo [INFO] Checking scheduled task...

schtasks /Query /TN "%TASK_NAME%" >nul 2>&1

if errorlevel 1 (
    echo [INFO] Scheduled task was not found.
    echo [INFO] Nothing to uninstall.
    echo.
    pause
    exit /b 0
)

echo [INFO] Scheduled task found:
echo        %TASK_NAME%
echo.

echo [INFO] Removing scheduled task...

schtasks /Delete /TN "%TASK_NAME%" /F

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to remove the scheduled task.
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] Verifying removal...

schtasks /Query /TN "%TASK_NAME%" >nul 2>&1

if not errorlevel 1 (
    echo [ERROR] Scheduled task still exists.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo      Uninstallation completed!
echo ========================================
echo.
echo Removed:
echo   %TASK_NAME%
echo.
echo The following were NOT removed:
echo   - config/config.json
echo   - logs/
echo   - Python environment
echo   - Windows PPPoE profile
echo.
echo [INFO] NTOU PPPoE Manager has been uninstalled.
echo.

pause

exit /b 0
