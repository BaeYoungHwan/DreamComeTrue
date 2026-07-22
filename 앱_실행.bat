@echo off
cd /d "%~dp0"
echo ============================================
echo   로컬 팜 인벤토리 시작 중...
echo   잠시 후 브라우저가 자동으로 열립니다.
echo   열리지 않으면 주소창에 http://localhost:8501 입력하세요.
echo   이 창을 닫으면 프로그램이 종료됩니다.
echo ============================================
python -m streamlit run app.py
echo.
echo 프로그램이 종료되었습니다.
pause
