@echo off
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Restarting with administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c, %~dp0%~nx0' -Verb RunAs"
    exit /b
)
echo Starting PostgreSQL 16 service...
net start postgresql-x64-16
if %errorlevel% neq 0 (
    echo Error starting PostgreSQL 16 service.
    pause
    exit /b
)
echo PostgreSQL 16 service started successfully.
pause
exit /b