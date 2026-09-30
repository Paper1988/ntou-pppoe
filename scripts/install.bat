@echo off
setlocal

cd /d "%~dp0.."

set "TASK_NAME=NTOU-PPPoE Manager"

:: Check for administrator privileges
net session >nul 2>&1

if errorlevel 1 (
    echo [INFO] Administrator privileges are required to install the scheduled task.
    echo [INFO] Requesting elevation...
    echo.

    powershell -NoProfile -Command ^
        "Start-Process -FilePath '%~f0' -Verb RunAs"

    exit /b 0
)

echo ========================================
echo          NTOU PPPoE Manager
echo             Installation
echo ========================================
echo.

where python >nul 2>&1

if errorlevel 1 (
    echo [ERROR] Python was not found in PATH.
    echo.
    echo Please install Python 3.11 or newer,
    echo then try again.
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%P in ('where python') do (
    set "PYTHON_PATH=%%P"
    goto :python_found
)

:python_found

if not defined PYTHON_PATH (
    echo [ERROR] Failed to determine the Python executable path.
    echo.
    pause
    exit /b 1
)

echo [INFO] Python:
echo        %PYTHON_PATH%
echo.

for %%D in ("%PYTHON_PATH%") do set "PYTHON_DIR=%%~dpD"

set "PYTHONW_PATH=%PYTHON_DIR%pythonw.exe"

if not exist "%PYTHONW_PATH%" (
    echo [ERROR] pythonw.exe was not found.
    echo.
    echo Expected:
    echo   %PYTHONW_PATH%
    echo.
    pause
    exit /b 1
)

echo [INFO] PythonW:
echo        %PYTHONW_PATH%
echo.

python -m ntou_pppoe --help >nul 2>&1

if errorlevel 1 (
    echo [ERROR] ntou_pppoe could not be started.
    echo.
    echo Make sure the project is installed with:
    echo.
    echo     python -m pip install -e .
    echo.
    pause
    exit /b 1
)

echo [INFO] ntou_pppoe is available.
echo.

schtasks /Query /TN "%TASK_NAME%" >nul 2>&1

if not errorlevel 1 (
    echo [INFO] Existing scheduled task found.
    echo [INFO] Removing old task...

    schtasks /Delete /TN "%TASK_NAME%" /F >nul

    if errorlevel 1 (
        echo [ERROR] Failed to remove the existing task.
        echo.
        pause
        exit /b 1
    )
)

echo [INFO] Creating scheduled task...

schtasks /Create ^
    /TN "%TASK_NAME%" ^
    /TR "\"%PYTHONW_PATH%\" -m ntou_pppoe start" ^
    /SC ONLOGON ^
    /RL LIMITED ^
    /F

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create the scheduled task.
    echo.
    echo Try running this script again.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo       Installation completed!
echo ========================================
echo.
echo Task:
echo   %TASK_NAME%
echo.
echo Trigger:
echo   At user logon
echo.
echo Command:
echo   "%PYTHONW_PATH%" -m ntou_pppoe start
echo.

schtasks /Query /TN "%TASK_NAME%" /FO LIST

echo.
echo [INFO] NTOU PPPoE Manager is now installed.
echo.

pause

exit /b 0
