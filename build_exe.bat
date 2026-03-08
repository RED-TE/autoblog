@echo off
chcp 65001 > nul
echo =======================================================
echo   🚀 RealCar Bot - 원클릭 EXE 빌드 스크립트
echo =======================================================
echo.

:: 1. PyInstaller 설치 확인 및 설치
echo [1/3] PyInstaller 설치 확인 중...
pip install pyinstaller

echo.
echo [2/3] 기존 빌드 파일 정리 중...
rmdir /s /q build
rmdir /s /q dist
del /q bot_app.spec

echo.
echo [3/3] EXE 빌드 시작! (약 1~3분 소요)
:: --onedir: 폴더 형태로 생성 (실행 속도 빠름)
:: --windowed: 검은색 콘솔 창 숨김
:: --add-data: 필요한 리소스 파일 포함
pyinstaller --noconfirm --onedir --windowed --icon=NONE --add-data "version.json;." bot_app.py

echo.
if exist "dist\bot_app\bot_app.exe" (
    echo =======================================================
    echo   🎉 빌드 성공! 
    echo   [dist\bot_app] 폴더 안에 bot_app.exe 가 생성되었습니다.
    echo =======================================================
    :: 바로 폴더 열어주기
    explorer "dist\bot_app"
) else (
    echo =======================================================
    echo   ❌ 빌드 실패. 에러 메시지를 확인해주세요.
    echo =======================================================
)

pause
