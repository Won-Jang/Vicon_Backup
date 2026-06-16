@echo off
REM Safe default: copy new/changed Vicon files from E: to F:. Does not delete from F:.
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%scripts\backup_vicon.py" --mode backup
pause
