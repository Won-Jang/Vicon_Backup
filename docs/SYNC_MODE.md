# Sync Mode

This project has three modes.

## 1. Backup mode

File:

```text
run_backup.bat
```

Behavior:

```text
E:\ → F:\
```

This copies new and changed files. It does not delete files from E or F.

Use this for regular Nexus post-capture backup.

## 2. Compare mode

File:

```text
run_compare.bat
```

This previews differences between E and F. It does not copy or delete files.

Use this before mirror sync.

## 3. Sync mirror mode

File:

```text
run_sync_mirror.bat
```

This makes the F-drive backup match the E-drive source.

Warning:

```text
Files on F that do not exist on E may be deleted.
```

Use this manually only when you intentionally want F to match E exactly.
