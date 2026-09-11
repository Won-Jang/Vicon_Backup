#!/usr/bin/env python3
"""
Vicon Backup Pipeline

Default use case:
    E:\\  ->  F:\\

Modes:
    write_once   Copy new files only. Does not overwrite existing destination files.
                 Official V1 mode for daily 10 PM Windows Task Scheduler backup.
    backup       Copy-only incremental backup. Copies new and changed files.
                 Kept for future Nexus pipeline use.
    compare      Dry comparison/listing. No copy, no delete.
    sync_mirror  Make destination match source. Can delete files from destination.
                 Future/manual use only.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "backup_config.json"

ROBOCOPY_SUCCESS_CODES = set(range(0, 8))


def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def drive_free_gb(path: Path) -> float:
    # The path does not need to exist if the drive/root exists.
    root = Path(path.anchor) if path.anchor else path
    usage = shutil.disk_usage(str(root))
    return usage.free / (1024 ** 3)


def build_robocopy_command(config: Dict[str, Any], mode: str, log_file: Path) -> List[str]:
    source = config["source_root"]
    dest = config["destination_root"]
    options = list(config.get("robocopy_options", {}).get(mode, []))

    cmd = ["robocopy", source, dest]
    cmd.extend(options)

    for d in config.get("excluded_dirs", []):
        cmd.extend(["/XD", d])
    for f in config.get("excluded_files", []):
        cmd.extend(["/XF", f])

    cmd.append(f"/LOG+:{log_file}")
    return cmd


def write_status(config: Dict[str, Any], mode: str, status: str, return_code: int, log_file: Path, message: str = "") -> Path | None:
    if not config.get("write_status_json", True):
        return None

    log_dir = Path(config.get("log_dir", PROJECT_ROOT / "logs"))
    ensure_dir(log_dir)
    status_path = log_dir / f"backup_status_{now_stamp()}.json"

    payload = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "source_root": config.get("source_root"),
        "destination_root": config.get("destination_root"),
        "status": status,
        "robocopy_return_code": return_code,
        "log_file": str(log_file),
        "message": message,
    }

    with status_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return status_path


def run(mode: str, config_path: Path) -> int:
    config = load_config(config_path)

    source = Path(config["source_root"])
    dest = Path(config["destination_root"])
    log_dir = Path(config.get("log_dir", PROJECT_ROOT / "logs"))
    ensure_dir(log_dir)

    log_file = log_dir / f"vicon_{mode}_{now_stamp()}.log"

    if not source.exists():
        msg = f"Source path does not exist: {source}"
        print(f"ERROR: {msg}")
        write_status(config, mode, "failed", 99, log_file, msg)
        return 99

    # For backup/sync modes, ensure destination exists before checking free space.
    if mode in {"write_once", "backup", "sync_mirror"}:
        ensure_dir(dest)
        min_free = float(config.get("minimum_free_space_gb", 0))
        try:
            free_gb = drive_free_gb(dest)
            if free_gb < min_free:
                msg = f"Destination free space is low: {free_gb:.1f} GB available, minimum required {min_free:.1f} GB."
                print(f"ERROR: {msg}")
                write_status(config, mode, "failed", 98, log_file, msg)
                return 98
        except Exception as exc:
            msg = f"Could not check destination free space: {exc}"
            print(f"WARNING: {msg}")

    if mode == "write_once":
        print("INFO: write_once mode copies only files that do not already exist at the destination.")
        print("Existing files on F are not overwritten, even if the E-drive version changes later.")

    if mode == "sync_mirror":
        print("WARNING: sync_mirror mode can delete files from the destination if they no longer exist in the source.")
        print("Use compare mode first before running sync_mirror.")

    cmd = build_robocopy_command(config, mode, log_file)
    print("Running:")
    print(" ".join(f'"{part}"' if " " in part else part for part in cmd))
    print()

    try:
        completed = subprocess.run(cmd, check=False)
        rc = completed.returncode
    except FileNotFoundError:
        msg = "Robocopy was not found. This script is intended to run on Windows."
        print(f"ERROR: {msg}")
        write_status(config, mode, "failed", 97, log_file, msg)
        return 97

    if rc in ROBOCOPY_SUCCESS_CODES:
        status = "success"
        msg = "Robocopy completed successfully or with non-fatal differences."
    else:
        status = "failed"
        msg = "Robocopy reported a failure. Check the log file."

    print(f"Status: {status}")
    print(f"Robocopy return code: {rc}")
    print(f"Log file: {log_file}")
    status_path = write_status(config, mode, status, rc, log_file, msg)
    if status_path:
        print(f"Status JSON: {status_path}")

    return 0 if status == "success" else rc


def main() -> int:
    parser = argparse.ArgumentParser(description="Vicon PC E-to-F backup/sync utility")
    parser.add_argument("--mode", choices=["write_once", "backup", "compare", "sync_mirror"], default="write_once")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    return run(args.mode, args.config)


if __name__ == "__main__":
    sys.exit(main())
