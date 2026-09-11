@echo off
setlocal
REM Vicon Daily Write-Once Backup
REM Official V1 automated workflow: copy new files from E to F without overwriting existing F files.

cd /d "%~dp0"
python scripts\backup_vicon.py --mode write_once --config config\backup_config.json
set EXITCODE=%ERRORLEVEL%
echo.
echo Daily write-once backup finished with exit code %EXITCODE%.
exit /B %EXITCODE%
