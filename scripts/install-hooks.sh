#!/bin/sh
# Install git hooks from the repository 'hooks' directory into .git/hooks
set -e
HOOKS_DIR="$(pwd)/hooks"
GIT_HOOKS_DIR=".git/hooks"

if [ ! -d "$GIT_HOOKS_DIR" ]; then
  echo "This repository doesn't appear to have a .git directory here. Run this from the repo root."
  exit 1
fi

for f in "$HOOKS_DIR"/*; do
  base=$(basename "$f")
  cp "$f" "$GIT_HOOKS_DIR/$base"
  chmod +x "$GIT_HOOKS_DIR/$base"
  echo "Installed $base -> $GIT_HOOKS_DIR/$base"
done

echo "Done."
