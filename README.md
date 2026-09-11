# Vicon Backup Pipeline

Small Windows backup utility for a Vicon Nexus PC.

## Current official workflow

The current V1 requirement is a **daily automated write-once backup** from the main Vicon data drive to the dedicated backup drive.

```text
E:\  ->  F:\
```

This backup runs outside of Nexus using Windows Task Scheduler. The recommended schedule is:

```text
Daily at 10:00 PM
```

This is **not true mirroring** and **not two-way sync**.

Once a file is copied to `F:`, it should stay there. Later changes on `E:` should not delete or overwrite the existing copy on `F:`.

## Vicon PC drive layout

```text
C: Windows OS, Vicon Nexus, MATLAB/Python, other software
D: temporary video cache / video processing
E: main working Vicon data storage
F: dedicated backup hard drive
```

## Main requirement

The `F:` drive is used as a backup-only drive for preserving collected Vicon data.

The backup should:

- Run automatically once per day at 10 PM.
- Copy new files from `E:` to `F:`.
- Not require the user to run a Nexus pipeline.
- Not slow down active data collection.
- Not delete files from `F:` if they are deleted from `E:`.
- Not overwrite files on `F:` if the same file is modified later on `E:`.
- Keep logs on the `F:` drive.

## Expected behavior

| Action on E drive | What happens on F drive |
|---|---|
| New file is created on E | Copied to F during nightly backup |
| File is deleted from E | Existing copy stays on F |
| File is renamed on E | Old copy stays on F; renamed file may copy as a new file |
| File content is modified on E | Existing F copy is not overwritten |
| New participant/session folder is created | Folder and files are copied to F |

## Files

```text
vicon-backup-pipeline/
├── README.md
├── run_daily_write_once_backup.bat
├── run_backup.bat
├── run_backup_dry_run.bat
├── run_compare.bat
├── run_sync_mirror.bat
├── config/
│   └── backup_config.json
├── docs/
│   ├── DAILY_WRITE_ONCE_BACKUP.md
│   ├── NEXUS_PIPELINE_SETUP.md
│   └── SYNC_MODE.md
├── logs/
└── scripts/
    └── backup_vicon.py
```

## Modes

### Daily write-once mode — official V1 mode

```text
run_daily_write_once_backup.bat
```

This copies only files that do not already exist on `F:`.

It does not overwrite existing files on `F:`, even if the file on `E:` was modified later.

This mode is intended for Windows Task Scheduler at 10 PM every day.

### Backup mode — future Nexus pipeline option

```text
run_backup.bat
```

This copies new and changed files from `E:` to `F:` but does not delete anything from either drive.

This mode is kept for future use if the lab later wants a Nexus post-capture pipeline backup.

### Dry run / compare mode

```text
run_backup_dry_run.bat
```

or

```text
run_compare.bat
```

This previews differences between the E drive source and F drive backup destination.

No files are copied or deleted.

### Sync mirror mode — future/manual use only

```text
run_sync_mirror.bat
```

This makes the F-drive destination match the E-drive source.

Warning: mirror mode can delete files from `F:` if those files no longer exist on `E:`.

Do not use this automatically. It is kept only for future/manual maintenance if needed.

## Installation

Copy this folder to the Vicon PC:

```text
C:\ViconTools\vicon-backup-pipeline
```

No separate destination subfolder is required because the current backup destination is the root of the F drive:

```text
F:\
```

The script will create the log folder automatically:

Edit the config file if needed:

```text
config\backup_config.json
```

Default config:

```json
{
  "source_root": "E:\\",
  "destination_root": "F:\\",
  "log_dir": "F:\\Vicon_Backup_Logs"
}
```

If the real Nexus data folder is different, update `source_root` and `destination_root`.

## First test

Run this first to confirm the script works:

```text
run_daily_write_once_backup.bat
```

Check logs here:

```text
F:\Vicon_Backup_Logs
```

## Windows Task Scheduler setup

Create a task with these settings:

```text
Task name:
Vicon Daily E to F Write-Once Backup

Trigger:
Daily at 10:00 PM

Action:
Start a program

Program:
C:\ViconTools\vicon-backup-pipeline\run_daily_write_once_backup.bat
```

Recommended task options:

```text
Run whether user is logged on or not
Run with highest privileges
Wake the computer to run this task
Stop the task if it runs longer than 6 hours
```

## Nexus pipeline setup — future use

The Nexus pipeline option is kept in this project for future use.

If the lab later wants Nexus to trigger a backup after capture/session work, add this file to the Nexus post-capture pipeline as an external application:

```text
C:\ViconTools\vicon-backup-pipeline\run_backup.bat
```

Do not use Nexus pipeline mode for the current V1 requirement. The current requirement is daily automated backup through Windows Task Scheduler.

## Backup drive note

The `F:` drive should be a dedicated backup drive. A 16TB or larger enterprise/datacenter SATA HDD is recommended for this role.

The program is based on the configured drive letter and folder path, not a specific hard drive model.

## Safety notes

- Do not back up `C:` as part of the regular data backup.
- Do not back up `D:` unless final video files are stored there.
- Keep `D:` as temporary video cache if possible.
- Keep final Vicon data and final video/session files on `E:`.
- Keep `F:` as backup only.
- Use daily write-once mode for the official V1 workflow.
- Keep Nexus pipeline mode and mirror mode only for future/manual use.

## Root-to-root path update

The current default path is now the full Vicon data drive to the full backup drive:

```text
E:\  ->  F:\
```

This means the backup copies new files and folders from the root of `E:` directly to the root of `F:`. Existing files already present on `F:` are not overwritten in the official write-once mode. Files deleted from `E:` are not deleted from `F:`.

Backup logs are written to:

```text
F:\Vicon_Backup_Logs
```
