#!/usr/bin/env python3
"""Update the BUILD_TS placeholder inside pocket.py with current YYMMDDHHMM timestamp.

Usage: python3 scripts/update_build_ts.py [path/to/pocket.py]
This script replaces the digits after the "Pocket 1.3 is ready. <<<<" text.
"""
import sys
import re
from datetime import datetime
from pathlib import Path

fmt = "%y%m%d%H%M"
ts = datetime.now().strftime(fmt)

p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("pocket.py")
if not p.exists():
    print(f"File not found: {p}")
    sys.exit(2)

text = p.read_text()
lines = text.splitlines()
changed = False
for i, line in enumerate(lines):
    if "Pocket is ready" in line:
        # Replace any digits previously inserted after the marker
        new_line = re.sub(r'(>>>> cPocket is ready.. \ )\s*\d*', r'\1 ' + ts, line)
        if new_line != line:
            lines[i] = new_line
            changed = True
# If we changed at least one line, write the file back
if changed:
    new_text = "\n".join(lines)
    if text.endswith("\n"):
        new_text = new_text + "\n"
    p.write_text(new_text)
    print(f"Updated {p} with timestamp {ts}")
    try:
        import subprocess
        subprocess.run(["git", "add", str(p)], check=True)
    except Exception:
        pass
    sys.exit(0)

# No line contained the marker; print diagnostics to help the user
print("No target line found to update (expected a 'Pocket 1.3 is ready' line).")
# Show any lines containing 'Pocket' or 'ready' to help debug
found = False
for i, line in enumerate(lines, start=1):
    if 'Pocket' in line or 'ready' in line:
        print(f"{i}: {line!r}")
        found = True
if not found:
    print("No 'Pocket' or 'ready' tokens found in the file. Check the file path.")
print("Run from repo root: python3 scripts/update_build_ts.py pocket.py")
print("Or from scripts/: python3 update_build_ts.py ../pocket.py")
sys.exit(1)
