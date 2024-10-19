@echo off
cd .
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%PYTHONPATH%;.
python -m create_db
pause
 