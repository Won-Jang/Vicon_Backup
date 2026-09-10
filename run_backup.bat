@echo off
setlocal
cd /d "%~dp0"
python scripts\backup_vicon.py --mode backup --config config\backup_config.json
set EXITCODE=%ERRORLEVEL%
echo.
echo Backup finished with exit code %EXITCODE%.
exit /B %EXITCODE%
