# Vicon Backup Pipeline

Small Windows backup/sync utility for a Vicon Nexus PC.

This project is designed for a Vicon PC with this drive layout:

```text
C: Windows OS, Vicon Nexus, MATLAB/Python, other software
D: temporary video cache / video processing
E: main Vicon data storage
F: dedicated backup hard drive
```

The regular backup direction is:

```text
E:\ViconData  →  F:\Vicon_Backup\ViconData
```

## Purpose

The goal is to back up Vicon motion tracking data and video/session files after each session or capture.

Recommended design:

```text
Nexus capture/session ends
  ↓
Nexus saves data to E drive
  ↓
Nexus post-capture pipeline runs run_backup.bat
  ↓
Data is copied from E drive to F drive
  ↓
Backup log/status file is written
```

## Files

```text
vicon-backup-pipeline/
├── README.md
├── run_backup.bat
├── run_backup_dry_run.bat
├── run_compare.bat
├── run_sync_mirror.bat
├── config/
│   └── backup_config.json
├── docs/
│   ├── NEXUS_PIPELINE_SETUP.md
│   └── SYNC_MODE.md
├── logs/
└── scripts/
    └── backup_vicon.py
```

## Modes

### Backup mode

```text
run_backup.bat
```

Safe copy-only incremental backup.

It copies new and changed files from `E:` to `F:` but does not delete anything from either drive.

Use this as the regular Nexus post-capture backup mode.

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

### Sync mirror mode

```text
run_sync_mirror.bat
```

This makes the F-drive backup match the E-drive source.

Warning: mirror mode can delete files from `F:` if those files no longer exist on `E:`.

Do not use this automatically in the Nexus pipeline. Use it manually only after running compare mode.

## Installation

Copy this folder to the Vicon PC:

```text
C:\ViconTools\vicon-backup-pipeline
```

Create the backup folder on the F drive:

```text
F:\Vicon_Backup
```

Edit the config file if needed:

```text
config\backup_config.json
```

Default config:

```json
{
  "source_root": "E:\\ViconData",
  "destination_root": "F:\\Vicon_Backup\\ViconData",
  "log_dir": "F:\\Vicon_Backup\\logs"
}
```

If the real Nexus data folder is different, update `source_root` and `destination_root`.

## First test

Run this first:

```text
run_backup_dry_run.bat
```

Then run the real backup:

```text
run_backup.bat
```

Check logs here:

```text
F:\Vicon_Backup\logs
```

## Nexus pipeline setup

After manual testing works, add this file to the Nexus post-capture pipeline as an external application:

```text
C:\ViconTools\vicon-backup-pipeline\run_backup.bat
```

Use only `run_backup.bat` for the automatic Nexus pipeline.

## Backup drive note

The `F:` drive should be a dedicated backup drive. A 16TB or larger enterprise/datacenter SATA HDD is recommended for this role.

The program is based on the configured drive letter and folder path, not a specific hard drive model.

## Safety notes

- Do not back up `C:` as part of the regular session backup.
- Do not back up `D:` unless final video files are stored there.
- Keep `D:` as temporary video cache if possible.
- Keep final Vicon data and final video/session files on `E:`.
- Keep `F:` as backup only.
- Use backup mode for normal daily work.
- Use mirror sync only as a manual maintenance tool.
