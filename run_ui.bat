@echo off
chcp 65001 > nul
echo.
echo  ========================================
echo   블로그 자동화 봇 UI 시작
echo  ========================================
echo.
cd /d "%~dp0"
call venv\Scripts\activate.bat 2>nul || (
    echo [오류] 가상환경 없음 - 직접 실행합니다
)
echo  UI 시작 중... (브라우저가 자동으로 열립니다)
echo.
streamlit run bot_ui.py --server.port 8502 --server.headless false
pause
