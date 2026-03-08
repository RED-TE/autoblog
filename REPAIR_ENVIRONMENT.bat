@echo off
setlocal
echo ====================================================
echo   [Naver Bot] Environment Repair & Clean Setup
echo ====================================================
echo.

echo [1/4] Checking for existing environment...
if exist venv (
    echo   - Deleting old 'venv' folder...
    rmdir /s /q venv
)

echo [2/4] Recreating Virtual Environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: Failed to create venv. Make sure Python is installed.
    pause
    exit /b
)

echo [3/4] Installing Required Libraries (This may take a minute)...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install setuptools wheel
pip install pyperclip numpy beautifulsoup4 streamlit selenium requests google-generativeai fake-useragent pillow undetected-chromedriver

if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: Installation failed. Check your internet connection.
    pause
    exit /b
)

echo [4/4] Verifying Installation...
python -c "import fake_useragent; import undetected_chromedriver; print('✅ Verification SUCCESS: All libraries ready.')"
if %errorlevel% neq 0 (
    echo ❌ ERROR: Verification failed.
)

echo.
echo ====================================================
echo   ✨ REPAIR COMPLETE! 
echo   Please run 'run_bot.bat' to start the bot.
echo ====================================================
pause
