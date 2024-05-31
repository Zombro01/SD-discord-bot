@echo off
echo Setting up your Discord bot environment...

REM Check for Python installation
python --version
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python and try again.
    exit /b 1
)

REM Upgrade pip
python -m pip install --upgrade pip

REM Install required packages globally, each on a separate line
pip install discord.py
pip install requests
pip install pillow
pip install aiohttp

echo Setup complete! All necessary packages have been installed globally.