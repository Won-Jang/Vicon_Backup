# Daily Write-Once Backup Requirement

This is the official V1 backup requirement for the Vicon PC.

## Requirement

The backup should run automatically once per day without requiring a Nexus pipeline.

Recommended schedule:

```text
Daily at 10:00 PM
```

Backup direction:

```text
E:\  ->  F:\
```

## Drive roles

```text
C: Windows OS, Nexus, MATLAB/Python, other software
D: video cache / temporary video processing
E: main working Vicon data drive
F: dedicated backup drive only
```

## Required behavior

This is not true mirroring and not two-way sync.

The backup must:

- Copy new files from `E:` to `F:`.
- Keep existing files on `F:`.
- Not delete files from `F:` if they are deleted from `E:`.
- Not overwrite files on `F:` if the same file is later modified on `E:`.
- Run outside of Nexus using Windows Task Scheduler.

## Behavior table

| Action on E drive | Result on F drive |
|---|---|
| New file is created | File is copied to F during the next backup |
| File is deleted | Existing F copy stays on F |
| File is renamed | Old F copy stays; renamed file may copy as a new file |
| File content is modified | Existing F copy is not overwritten |
| New participant/session folder is created | Folder and files are copied to F |

## Official V1 launcher

Use:

```text
run_daily_write_once_backup.bat
```

This calls:

```text
python scripts\backup_vicon.py --mode write_once
```

## Robocopy behavior

The write-once mode uses these key Robocopy options:

```text
/XC  Exclude changed files
/XN  Exclude newer source files
/XO  Exclude older source files
```

Together, these prevent existing files on `F:` from being overwritten.

## Task Scheduler setup

Create a Windows Task Scheduler task:

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

## Future options

The older Nexus pipeline mode and mirror/sync tools are kept in this project for possible future use, but they are not the official V1 automated workflow.
