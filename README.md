# Vicon Backup Pipeline

A small Windows-friendly backup pipeline for a Vicon Nexus PC.

The goal is to automatically back up motion tracking data and video files after each session or capture workflow, while keeping Nexus data safe and untouched.

## Current Vicon PC drive layout

```text
C: Windows OS, Nexus, Vicon software, MATLAB/Python, other programs
D: Video cache / temporary processing drive
E: Main Vicon data storage
F: New dedicated backup hard drive
```

## Backup policy

The default backup direction is:

```text
E:\ViconData  ->  F:\Vicon_Backup\ViconData
```

This project intentionally excludes the normal session backup from:

```text
C: system/program drive
D: temporary video cache drive
```

The backup is copy-only and incremental. It copies new or changed files from `E:` to `F:` but does not delete source files and does not mirror-delete files from the backup drive.

## Why this design

Vicon Nexus supports customized pipelines that can run automatically after capture or be run manually on saved trials. Nexus also supports running external applications from a pipeline operation, which makes it practical to let Nexus trigger this backup script after a capture/session. The file copy itself is handled outside Nexus so it can be logged, tested, and maintained independently.

## Project structure

```text
vicon-backup-pipeline/
├── README.md
├── run_backup.bat
├── run_backup_dry_run.bat
├── config/
│   └── backup_config.json
├── docs/
│   └── NEXUS_PIPELINE_SETUP.md
├── logs/
└── scripts/
    └── backup_vicon.py
```

## Quick start

### 1. Copy the project to the Vicon PC

Recommended location:

```text
C:\ViconTools\vicon-backup-pipeline
```

### 2. Edit the config file

Open:

```text
config\backup_config.json
```

Default settings:

```json
{
  "source_root": "E:\\ViconData",
  "backup_root": "F:\\Vicon_Backup\\ViconData",
  "log_dir": "F:\\Vicon_Backup\\logs"
}
```

Change `source_root` if the actual Nexus database folder on `E:` uses a different name.

Example:

```json
"source_root": "E:\\LisaLab_Nexus"
```

### 3. Run a dry-run test

Double-click:

```text
run_backup_dry_run.bat
```

This lists what would be copied without actually copying files.

### 4. Run the backup manually

Double-click:

```text
run_backup.bat
```

Check:

```text
F:\Vicon_Backup\logs
```

You should see log files and status JSON files.

## Nexus post-capture setup

Create a Nexus post-capture pipeline named something like:

```text
PostCapture_Backup_To_F_Drive
```

Add a **Run External Application** operation.

Recommended target:

```text
C:\ViconTools\vicon-backup-pipeline\run_backup.bat
```

See:

```text
docs\NEXUS_PIPELINE_SETUP.md
```

## Configuration options

Main config file:

```text
config\backup_config.json
```

Important fields:

| Field | Purpose |
|---|---|
| `source_root` | Main Vicon data folder on `E:` |
| `backup_root` | Backup destination on `F:` |
| `log_dir` | Backup log/status folder |
| `copy_mode` | Currently copy-only incremental backup |
| `use_robocopy_on_windows` | Uses Robocopy on Windows for reliability |
| `exclude_dirs` | Folder names to skip |
| `exclude_files` | File patterns to skip |
| `wait_for_file_stability_seconds` | Wait/check period before copying |
| `minimum_free_space_gb` | Safety check for available space on `F:` |
| `dry_run` | If true, list copy operations without copying |

## Copy engine

On Windows, this script uses Robocopy by default.

Default Robocopy options:

```text
/E /Z /COPY:DAT /DCOPY:DAT /R:2 /W:5 /NP
```

Meaning:

| Option | Meaning |
|---|---|
| `/E` | Copy subfolders, including empty folders |
| `/Z` | Restartable copy mode |
| `/COPY:DAT` | Copy data, attributes, and timestamps |
| `/DCOPY:DAT` | Preserve directory data, attributes, and timestamps |
| `/R:2` | Retry twice on failed copies |
| `/W:5` | Wait 5 seconds between retries |
| `/NP` | No progress percentage in log |

This project does **not** use `/MIR` by default because mirror mode can delete files from the backup if files are removed from the source.

## Output files

Each run writes files to:

```text
F:\Vicon_Backup\logs
```

Example:

```text
vicon_backup_2026-06-16_14-30-10.log
vicon_backup_status_2026-06-16_14-30-10.json
vicon_backup_history.csv
```

Example status JSON:

```json
{
  "timestamp": "2026-06-16T14:30:10",
  "source": "E:\\ViconData",
  "destination": "F:\\Vicon_Backup\\ViconData",
  "status": "success",
  "exit_code": 1,
  "free_space_gb_before": 1800.5,
  "free_space_gb_after": 1779.2,
  "dry_run": false
}
```

## Recommended lab workflow

```text
1. Lab opens Nexus.
2. Lab captures trials normally.
3. Nexus saves trial/session data to E:.
4. Nexus post-capture pipeline runs the backup script.
5. Script copies E: data to F:.
6. Script writes log/status files to F:\Vicon_Backup\logs.
```

## Safety notes

- This backup script does not delete original Nexus data.
- This backup script does not modify the `E:` drive data.
- The `D:` drive is treated as temporary cache and is not backed up by default.
- If final synchronized videos are stored on `D:` instead of `E:`, either change Nexus/video settings so final video files save to `E:`, or add a second source folder later.
- Run the dry-run test before enabling automatic Nexus pipeline execution.

## Development roadmap

### Version 0.1

- Copy-only backup from `E:` to `F:`
- Configurable source/destination
- Robocopy support on Windows
- Dry-run mode
- Log files
- JSON status output
- CSV backup history

### Version 0.2 ideas

- Detect current Nexus trial/session folder through Nexus API
- Copy only the active session instead of the whole source root
- Add simple desktop notification after success/failure
- Add optional nightly archive to NAS/server
- Add email or Teams notification on backup failure
- Add GUI config editor for lab staff

## License

Internal lab/development use. Add an official license before making the repository public.

## E-to-F sync feature

This project now supports both the original safe backup workflow and an optional one-way sync workflow.

### Available modes

| Mode | Direction | Deletes from F:? | Use case |
|---|---|---:|---|
| `backup` | `E:` -> `F:` | No | Safe default after each Nexus capture/session |
| `compare` | Preview only | No | Check differences between E and F before syncing |
| `sync_mirror` | `E:` -> `F:` | Yes | Make F match E exactly during maintenance |

### Recommended daily Nexus mode

Use this from the Nexus post-capture pipeline:

```text
run_backup.bat
```

This keeps the backup copy-only and does not delete anything from the backup drive.

### Preview E/F differences

Run:

```text
run_compare.bat
```

This uses preview/list mode. It does not copy or delete files. Check the generated log under:

```text
F:\Vicon_Backup\logs
```

### One-way mirror sync

Run:

```text
run_sync_mirror.bat
```

This makes the destination on `F:` match the source on `E:`. This mode can delete files from `F:` that no longer exist on `E:`.

Use this only after running `run_compare.bat` and reviewing the log.

### Why not two-way sync?

For Vicon/Nexus data, two-way sync is not recommended as the default because it can create conflicts, copy older files back into the active data drive, or restore files that were intentionally removed. The safer design is one-directional:

```text
E: active Nexus data source
F: backup/mirror destination
```

More detail:

```text
docs\SYNC_MODE.md
```
