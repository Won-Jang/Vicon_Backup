@echo off
REM Preview differences between E: Vicon data and F: backup. No files are copied or deleted.
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%scripts\backup_vicon.py" --mode compare
pause
