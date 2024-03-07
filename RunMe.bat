@echo off
setlocal enabledelayedexpansion

rem Check if Python is installed
python3 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install it and try again.
    echo Download Python by pressing Enter.
    pause >nul
    start "" "https://apps.microsoft.com/detail/9NRWMJP3717K?hl=fr-ca&gl=US"
    exit /b
)

rem Install setuptools if not already installed
python -m pip install setuptools >nul 2>&1
if %errorlevel% neq 0 (
    echo An error occurred during the installation of setuptools.
    pause
    exit /b
)

rem Check if the required Python modules are installed
python -c "import pkg_resources" >nul 2>&1
if %errorlevel% neq 0 (
    echo An error occurred while checking for pkg_resources.
    pause
    exit /b
)

rem Install Python dependencies one by one from requirements.txt
for /F %%i in (requirements.txt) do (
    pip install %%i
    if !errorlevel! neq 0 (
        echo An error occurred during the installation of the dependency %%i.
        pause
        exit /b
    ) else (
        powershell -command "$Host.UI.RawUI.ForegroundColor = 'Green'; Write-Host 'Successfully installed the dependency %%i.'; $Host.UI.RawUI.ForegroundColor = 'White'"
    )
)

echo All Python dependencies have been successfully installed.

rem Launch the Python script
python VRCST.py

rem Pause to display results (you can remove this if you wish)
pause
