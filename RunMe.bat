@echo off
setlocal enabledelayedexpansion

rem Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install it and try again.
    echo Download Python by pressing Enter.
    pause >nul
    start "" "https://apps.microsoft.com/detail/9NRWMJP3717K?hl=fr-ca&gl=US"
    exit /b
)

rem Install setuptools if not already installed
echo Checking for setuptools...
python -m pip show setuptools >nul 2>&1
if %errorlevel% neq 0 (
    echo setuptools not found. Installing setuptools...
    python -m pip install setuptools
    if %errorlevel% neq 0 (
        echo An error occurred during the installation of setuptools.
        pause
        exit /b
    )
) else (
    echo setuptools is already installed.
)

rem Check if the required Python modules are installed
echo Checking for required Python modules...
if not exist requirements.txt (
    echo requirements.txt file not found.
    pause
    exit /b
)

for /F "usebackq tokens=*" %%i in ("requirements.txt") do (
    echo Checking for %%i...
    python -m pip show %%i >nul 2>&1
    if %errorlevel% neq 0 (
        echo Installing %%i...
        pip install %%i
        if !errorlevel! neq 0 (
            echo An error occurred during the installation of the dependency %%i.
            pause
            exit /b
        ) else (
            powershell -command "$Host.UI.RawUI.ForegroundColor = 'Green'; Write-Host 'Successfully installed the dependency %%i.'; $Host.UI.RawUI.ForegroundColor = 'White'"
        )
    ) else (
        echo %%i is already installed.
    )
)

echo All Python dependencies have been successfully installed.

rem Launch the Python script
python VRCST.py

rem Pause to display results (you can remove this if you wish)
pause
