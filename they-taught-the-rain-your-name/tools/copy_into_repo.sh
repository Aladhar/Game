#!/usr/bin/env bash
set -euo pipefail

REPO_PATH="${1:-}"
if [ -z "$REPO_PATH" ]; then
  echo "Usage: ./tools/copy_into_repo.sh /path/to/Roblox"
  exit 1
fi

TARGET="$REPO_PATH/they-taught-the-rain-your-name"
mkdir -p "$TARGET"
rsync -av --exclude='.godot' ./ "$TARGET/"
echo "Copied project into: $TARGET"
