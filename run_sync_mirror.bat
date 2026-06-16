@echo off
REM One-way sync: make F: match E:. WARNING: this can delete files from F: that are not on E:.
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%scripts\backup_vicon.py" --mode sync_mirror --allow-delete
pause
