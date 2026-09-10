@echo off
setlocal
cd /d "%~dp0"
echo WARNING: This mode makes the F-drive backup match the E-drive source.
echo Files on F that do not exist on E may be deleted.
echo.
choice /M "Continue with sync mirror"
if errorlevel 2 exit /B 1
python scripts\backup_vicon.py --mode sync_mirror --config config\backup_config.json
set EXITCODE=%ERRORLEVEL%
echo.
echo Sync mirror finished with exit code %EXITCODE%.
exit /B %EXITCODE%
