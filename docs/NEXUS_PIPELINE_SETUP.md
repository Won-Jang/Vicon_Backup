# Nexus Pipeline Setup

Recommended Nexus use:

```text
Capture/session ends
  ↓
Nexus saves trial/session data to E:
  ↓
Nexus post-capture pipeline runs external application
  ↓
run_backup.bat copies E:\ to F:\
```

## Recommended external command

Copy the project folder to:

```text
C:\ViconTools\vicon-backup-pipeline
```

In Nexus, add a post-capture pipeline operation that runs this external application:

```text
C:\ViconTools\vicon-backup-pipeline\run_backup.bat
```

## Recommended mode for Nexus

Use only:

```text
run_backup.bat
```

Do not use `run_sync_mirror.bat` automatically in Nexus because mirror mode can delete files from the F drive.

## First test

Before adding it to Nexus, run these manually from File Explorer or Command Prompt:

```text
run_backup_dry_run.bat
run_backup.bat
```

Check logs in:

```text
F:\Vicon_Backup_Logs
```
