@echo off
echo Fixing environment and missing libraries...
call venv\Scripts\activate.bat
pip install setuptools
pip install pyperclip numpy beautifulsoup4 streamlit selenium requests google-generativeai fake-useragent pillow undetected-chromedriver
echo.
echo Fix complete! Try running 'run_bot.bat' again.
pause
