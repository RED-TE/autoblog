@echo off
echo Starting Dashboard...
call venv\Scripts\activate.bat
python -m streamlit run dashboard.py
pause
