# Sync Mode

This project has three modes:

| Mode | Direction | Deletes from F:? | Recommended use |
|---|---|---:|---|
| `backup` | `E:` -> `F:` | No | Default Nexus post-capture backup |
| `compare` | `E:` vs `F:` preview | No | Check what would change before syncing |
| `sync_mirror` | `E:` -> `F:` | Yes | Maintenance only, after reviewing compare mode |

## Recommended policy

Use `backup` from the Nexus post-capture pipeline. This is copy-only and safest for lab data.

Use `compare` manually when you want to inspect differences between the main Vicon data drive and backup drive.

Use `sync_mirror` only when you intentionally want the backup drive to match the current E drive exactly.

## Important warning

`sync_mirror` uses Robocopy `/MIR` on Windows. `/MIR` can delete files from the destination (`F:`) when those files no longer exist on the source (`E:`).

That is useful for a true mirror, but it is not the safest daily backup behavior.

## Recommended workflow

1. Run:

```text
run_compare.bat
```

2. Review the log in:

```text
F:\Vicon_Backup\logs
```

3. Only if the preview looks correct, run:

```text
run_sync_mirror.bat
```

## Command-line examples

Safe backup:

```text
python scripts\backup_vicon.py --mode backup
```

Preview only:

```text
python scripts\backup_vicon.py --mode compare
```

One-way mirror sync:

```text
python scripts\backup_vicon.py --mode sync_mirror --allow-delete
```

## What not to do

Do not use two-way sync for Nexus data unless there is a very specific reason. Two-way sync can create conflicts, overwrite newer files, or accidentally bring old/deleted files back into the active Nexus data folder.

For this Vicon PC, the clean design is:

```text
E: active/main Vicon data
F: backup/mirror destination
```
