@echo off
echo [Step 1] Cleaning up old environment...
if exist venv (
    rmdir /s /q venv
    echo Old venv deleted.
)

echo [Step 2] Creating new virtual environment...
python -m venv venv

echo [Step 3] Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install setuptools
pip install setuptools
pip install setuptools
pip install pyperclip numpy beautifulsoup4 streamlit
pip install selenium requests google-generativeai fake-useragent pillow undetected-chromedriver

echo.
echo [Success] Environment setup complete!
echo You can now run 'run_bot.bat' to start the bot.
pause
