@echo off
REM Safe preview of backup mode. No files are copied or deleted.
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%scripts\backup_vicon.py" --mode backup --dry-run
pause
