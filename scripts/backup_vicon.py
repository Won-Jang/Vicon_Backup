#!/usr/bin/env python3
"""
Vicon Backup Pipeline

Backup/sync utility from the Vicon data drive to a dedicated backup drive.
Designed to be called manually, by Windows Task Scheduler, or by a Vicon Nexus
post-capture pipeline using Run External Application.

Modes:
  backup       Copy-only incremental backup. Safe default. Does not delete from F:.
  compare      Preview differences between E: and F:. No files copied/deleted.
  sync_mirror  One-way E: -> F: mirror. Can delete extra files from F:. Use carefully.

Default drive design:
  C: OS + Nexus + software
  D: video cache/temp processing only
  E: source Vicon data storage
  F: backup destination
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import fnmatch
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


SUCCESS_EXIT_CODES = {0, 1, 2, 3, 5, 6, 7}
# Robocopy exit codes < 8 are typically non-fatal. 8+ indicates failure.
SAFE_MODES = {"backup", "compare", "sync_mirror"}


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def bytes_to_gb(value: int) -> float:
    return round(value / (1024**3), 2)


def get_free_space_gb(path: Path) -> float:
    # Use nearest existing parent so first-time backup folders work.
    probe = path
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    usage = shutil.disk_usage(probe)
    return bytes_to_gb(usage.free)


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def should_exclude(path: Path, exclude_dirs: list[str], exclude_files: list[str]) -> bool:
    parts = set(path.parts)
    for d in exclude_dirs:
        if d in parts:
            return True
    if path.is_file():
        return any(fnmatch.fnmatch(path.name, pattern) for pattern in exclude_files)
    return False


def wait_for_stable_tree(source: Path, seconds: int) -> None:
    """Basic safeguard so the script does not begin while files are still being written."""
    if seconds <= 0:
        return

    def snapshot() -> tuple[int, int]:
        total_size = 0
        file_count = 0
        for root, _, files in os.walk(source):
            for name in files:
                p = Path(root) / name
                try:
                    stat = p.stat()
                except OSError:
                    continue
                total_size += stat.st_size
                file_count += 1
        return file_count, total_size

    first = snapshot()
    time.sleep(seconds)
    second = snapshot()
    if first != second:
        time.sleep(seconds)


def build_robocopy_options(config: dict[str, Any], mode: str) -> list[str]:
    """Build Robocopy options for backup, compare, or one-way mirror sync."""
    if mode == "sync_mirror":
        # /MIR is equivalent to /E + /PURGE. It makes destination match source.
        # This is intentionally separate from default backup mode because it can
        # delete destination files that are no longer present in the source.
        return config.get("robocopy_sync_mirror_options", ["/MIR", "/Z", "/COPY:DAT", "/DCOPY:DAT", "/R:2", "/W:5", "/NP"])
    return config.get("robocopy_backup_options", config.get("robocopy_options", []))


def run_robocopy(source: Path, dest: Path, log_file: Path, config: dict[str, Any], mode: str) -> int:
    options = build_robocopy_options(config, mode)
    exclude_dirs = config.get("exclude_dirs", [])
    exclude_files = config.get("exclude_files", [])
    dry_run = bool(config.get("dry_run", False)) or mode == "compare"

    cmd = ["robocopy", str(source), str(dest), "*.*", *options]

    if exclude_dirs:
        cmd.extend(["/XD", *exclude_dirs])
    if exclude_files:
        cmd.extend(["/XF", *exclude_files])
    if dry_run and "/L" not in cmd:
        cmd.append("/L")

    cmd.append(f"/LOG+:{log_file}")

    print("Running:", " ".join(cmd))
    completed = subprocess.run(cmd, shell=False)
    return completed.returncode

def copy_with_python(source: Path, dest: Path, log_file: Path, config: dict[str, Any], mode: str) -> int:
    """Fallback copy engine for development/testing outside Windows."""
    exclude_dirs = config.get("exclude_dirs", [])
    exclude_files = config.get("exclude_files", [])
    dry_run = bool(config.get("dry_run", False)) or mode == "compare"
    copied = 0
    skipped = 0
    deleted = 0
    errors = 0

    with log_file.open("a", encoding="utf-8") as log:
        log.write(f"\n[{dt.datetime.now().isoformat()}] Python copy started\n")
        for root, dirs, files in os.walk(source):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not should_exclude(root_path / d, exclude_dirs, exclude_files)]
            rel_root = root_path.relative_to(source)
            target_root = dest / rel_root
            if not dry_run:
                target_root.mkdir(parents=True, exist_ok=True)

            for name in files:
                src = root_path / name
                if should_exclude(src, exclude_dirs, exclude_files):
                    continue
                dst = target_root / name
                try:
                    if dst.exists() and dst.stat().st_size == src.stat().st_size and int(dst.stat().st_mtime) >= int(src.stat().st_mtime):
                        skipped += 1
                        continue
                    log.write(f"COPY {src} -> {dst}\n")
                    if not dry_run:
                        shutil.copy2(src, dst)
                    copied += 1
                except OSError as exc:
                    errors += 1
                    log.write(f"ERROR {src}: {exc}\n")
        if mode == "sync_mirror":
            # Remove files from destination that no longer exist in source.
            for root, dirs, files in os.walk(dest):
                root_path = Path(root)
                dirs[:] = [d for d in dirs if not should_exclude(root_path / d, exclude_dirs, exclude_files)]
                rel_root = root_path.relative_to(dest)
                source_root = source / rel_root
                for name in files:
                    dst = root_path / name
                    src = source_root / name
                    if should_exclude(dst, exclude_dirs, exclude_files):
                        continue
                    if not src.exists():
                        log.write(f"DELETE {dst}\n")
                        if not dry_run:
                            try:
                                dst.unlink()
                            except OSError as exc:
                                errors += 1
                                log.write(f"ERROR DELETE {dst}: {exc}\n")
                                continue
                        deleted += 1
        log.write(f"Copied={copied}, skipped={skipped}, deleted={deleted}, errors={errors}\n")
    return 0 if errors == 0 else 8


def write_status(status_file: Path, data: dict[str, Any]) -> None:
    ensure_dir(status_file.parent)
    with status_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def append_history(csv_file: Path, row: dict[str, Any]) -> None:
    ensure_dir(csv_file.parent)
    fieldnames = [
        "timestamp", "source", "destination", "status", "exit_code",
        "free_space_gb_before", "free_space_gb_after", "dry_run"
    ]
    exists = csv_file.exists()
    with csv_file.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser(description="Back up or sync Vicon data from E: to F: with logging/status output.")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "backup_config.json"))
    parser.add_argument("--mode", choices=sorted(SAFE_MODES), help="backup=safe copy-only, compare=preview only, sync_mirror=make F match E")
    parser.add_argument("--allow-delete", action="store_true", help="Required for sync_mirror mode because it can delete extra files from F:.")
    parser.add_argument("--source", help="Override source folder, e.g. E:\\ViconData\\Subject01\\Session01")
    parser.add_argument("--dest", help="Override destination folder, e.g. F:\\Vicon_Backup\\ViconData\\Subject01\\Session01")
    parser.add_argument("--dry-run", action="store_true", help="List files without copying.")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)
    if args.dry_run:
        config["dry_run"] = True

    mode = args.mode or config.get("copy_mode", "backup")
    if mode == "incremental_copy_only":
        mode = "backup"
    if mode not in SAFE_MODES:
        raise ValueError(f"Unsupported mode: {mode}")
    if mode == "sync_mirror" and not args.allow_delete and not config.get("allow_delete_in_sync_mirror", False):
        raise RuntimeError("sync_mirror can delete files from F:. Re-run with --allow-delete after reviewing compare mode.")

    source = Path(args.source or config["source_root"])
    dest = Path(args.dest or config["backup_root"])
    log_dir = Path(config.get("log_dir", str(dest / "logs")))
    ensure_dir(log_dir)

    stamp = now_stamp()
    log_file = log_dir / f"vicon_backup_{stamp}.log"
    status_file = log_dir / f"vicon_backup_status_{stamp}.json"
    history_file = log_dir / "vicon_backup_history.csv"

    status: dict[str, Any] = {
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "source": str(source),
        "destination": str(dest),
        "config": str(config_path),
        "dry_run": bool(config.get("dry_run", False)),
        "status": "started",
        "mode": mode,
    }

    try:
        if not source.exists():
            raise FileNotFoundError(f"Source folder does not exist: {source}")

        free_before = get_free_space_gb(dest)
        status["free_space_gb_before"] = free_before
        min_free = float(config.get("minimum_free_space_gb", 0))
        if free_before < min_free:
            raise RuntimeError(f"Backup drive free space is {free_before} GB, below minimum {min_free} GB")

        wait_for_stable_tree(source, int(config.get("wait_for_file_stability_seconds", 0)))
        ensure_dir(dest)

        if is_windows() and config.get("use_robocopy_on_windows", True):
            exit_code = run_robocopy(source, dest, log_file, config, mode)
            ok = exit_code in SUCCESS_EXIT_CODES
        else:
            exit_code = copy_with_python(source, dest, log_file, config, mode)
            ok = exit_code == 0

        status["exit_code"] = exit_code
        status["free_space_gb_after"] = get_free_space_gb(dest)
        status["status"] = "success" if ok else "failed"
        write_status(status_file, status)
        append_history(history_file, status)
        label = "Compare" if mode == "compare" else ("Sync" if mode == "sync_mirror" else "Backup")
        print(f"{label} {status['status']}. Status: {status_file}")
        return 0 if ok else exit_code

    except Exception as exc:
        status["status"] = "failed"
        status["error"] = str(exc)
        try:
            write_status(status_file, status)
            append_history(history_file, status)
        finally:
            print(f"Vicon backup/sync failed: {exc}", file=sys.stderr)
        return 8


if __name__ == "__main__":
    raise SystemExit(main())
