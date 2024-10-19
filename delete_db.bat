@echo off
cd .
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%PYTHONPATH%;.
python -m delete_db
pause
