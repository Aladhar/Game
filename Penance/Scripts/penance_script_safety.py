"""Shared safety checks for scripts that can write Unreal or Blender assets."""

from __future__ import annotations

import os
import sys


ALLOW_ASSET_WRITE_ENV = "PENANCE_ALLOW_ASSET_WRITE"


def is_dry_run() -> bool:
    return "--dry-run" in sys.argv or os.environ.get("PENANCE_DRY_RUN") == "1"


def filtered_script_args(args: list[str]) -> list[str]:
    return [arg for arg in args if arg != "--dry-run"]


def require_asset_write_permission(action: str) -> None:
    if is_dry_run():
        print(f"DRY RUN: would {action}. No assets were modified.")
        raise SystemExit(0)

    if os.environ.get(ALLOW_ASSET_WRITE_ENV) == "1":
        return

    raise SystemExit(
        f"Refusing to {action}. Set {ALLOW_ASSET_WRITE_ENV}=1 for asset writes, "
        "or pass --dry-run to inspect the planned operation."
    )
