# Nexus Pipeline Setup

Recommended operation:

1. Open Nexus.
2. Go to the Pipeline tools area.
3. Create a new post-capture pipeline, for example: `PostCapture_Backup_To_F_Drive`.
4. Add the Nexus operation for running an external application.
5. Use one of these launch methods.

## Option A: Run the batch launcher

Program / executable:

```text
C:\ViconTools\vicon-backup-pipeline\run_backup.bat
```

Arguments:

```text
none
```

## Option B: Run Python directly

Program / executable:

```text
C:\Windows\py.exe
```

Arguments:

```text
-3 "C:\ViconTools\vicon-backup-pipeline\scripts\backup_vicon.py" --config "C:\ViconTools\vicon-backup-pipeline\config\backup_config.json"
```

## Test first

Before enabling automatic post-capture use, test with:

```text
run_backup_dry_run.bat
```

Then test manually with:

```text
run_backup.bat
```

Only after both tests look correct, add it to the Nexus post-capture pipeline.
