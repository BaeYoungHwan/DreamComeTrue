@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   최신 버전으로 업데이트합니다...
echo ============================================
git pull origin master
if errorlevel 1 (
    echo.
    echo [오류] 업데이트에 실패했습니다.
    echo 인터넷 연결을 확인하거나 개발자에게 문의하세요.
    pause
    exit /b 1
)

echo.
echo 필요한 프로그램을 설치합니다... (인터넷이 필요합니다)
python -m pip install -r requirements.txt --quiet

echo.
echo ============================================
echo   업데이트 완료! 이제 "앱_실행.bat"을 실행하세요.
echo ============================================
pause
