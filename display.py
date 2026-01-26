"""Display abstraction for SSD1309/SSD1306 OLED screens.

- Tries to use luma.oled (ssd1306) which is commonly available on RPi.
- Falls back to a no-op console logger if hardware libraries aren't present.

API:
- display.show_message(text)
- display.show_lines(list_of_lines)
- display.show_progress(message)  # non-blocking, simple text
- display.clear()
- display.close()

Keep behavior tolerant so the main runtime can run on macOS (dry-run) or on the Pi.
"""
import os

DRY_RUN = os.getenv("POCKET_DRY_RUN", "").lower() in ("1", "true", "yes")

# Default sizes for common small OLEDs (SSD1306/SSD1309)
WIDTH = 128
HEIGHT = 64

try:
    if DRY_RUN:
        raise RuntimeError("Dry run - do not initialize hardware display")

    # Try luma.oled first (stable on RPi with Pillow)
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import ssd1306
    from PIL import ImageFont

    serial = i2c(port=1, address=0x3C)
    device = ssd1306(serial, width=WIDTH, height=HEIGHT)
    #FONT = ImageFont.load_default()
    try:
        FONT = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 18)
        FONT_SMALL = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 12)
        # print('[display] Using FreeSans.ttf for both FONT and FONT_SMALL')
    except Exception as font_err:
        from PIL import ImageFont
        FONT = ImageFont.load_default()
        FONT_SMALL = ImageFont.load_default()
        # print(f'[display] Could not load FreeSans.ttf, using default font. Error: {font_err}')

    class _LumaDisplay:
        def __init__(self, device):
            self.device = device

        def show_lines(self, lines):
            # draw lines with simple vertical spacing
            with canvas(self.device) as draw:
                for i, line in enumerate(lines[: int(HEIGHT / 8)]):
                    draw.text((0, i * 20), str(line), font=FONT, fill="white")

        def show_message(self, text):
            self.show_lines([text])

        def show_progress(self, text):
            # Show progress with smaller font
            with canvas(self.device) as draw:
                draw.text((0, 0), str(text), font=FONT_SMALL, fill="white")

        def clear(self):
            with canvas(self.device) as draw:
                pass

        def close(self):
            try:
                self.device.cleanup()
            except Exception:
                pass

    display = _LumaDisplay(device)

except Exception as e:
    # Fallback dummy implementation that logs to stdout (useful for development or missing libs)
    import sys, traceback
    print("[display] Warning: failed to initialize luma display; using dummy backend.", file=sys.stderr)
    traceback.print_exc()

    class _DummyDisplay:
        def show_lines(self, lines):
            print("[display] " + " | ".join(str(x) for x in lines), file=sys.stderr)

        def show_message(self, text):
            print("[display] " + str(text), file=sys.stderr)

        def show_progress(self, text):
            print("[display-progress] " + str(text), file=sys.stderr)

        def clear(self):
            pass

        def close(self):
            pass

    display = _DummyDisplay()


# Convenience helpers (optional)

def show_selected(radio, model, name):
    title = f"R: {radio}"
    model_line = f"M: {model}" if model else ""
    details = f"F: {name}" if name else "Details:"
    lines = [title]
    if model_line:
        lines.append(model_line)
    lines.append(details)
    display.show_lines(lines)



def show_report(name, fname, radio=None):
    title = f"{name}"
    details = f"{fname}" if fname else "Details:"
    radio_line = f"{radio}" if radio else "Radio:"
    display.show_lines([title, details, radio_line])



def show_status(msg):
    display.show_message(msg)


def show_progress(msg):
    display.show_progress(msg)


def clear():
    display.clear()


def close():
    display.close()


# --- Streaming helpers and line buffer ---
from collections import deque
import subprocess

# Add append_line to the concrete display implementations if missing
try:
    # Luma display: add buffering and append_line method
    if hasattr(display, 'device') and not hasattr(display, 'append_line'):
        max_lines = max(1, HEIGHT // 8)
        # Monkey-patch append_line and show_lines behavior
        def _luma_append_line(line):
            display.lines.append(str(line))
            with canvas(display.device) as draw:
                for i, l in enumerate(list(display.lines)[-display.max_lines:]):
                    draw.text((0, i * 20), str(l), font=FONT, fill="white")
        def _luma_show_lines(lines):
            display.lines = deque([str(x) for x in lines][-display.max_lines:], maxlen=display.max_lines)
            with canvas(display.device) as draw:
                for i, l in enumerate(list(display.lines)):
                    draw.text((0, i * 20), str(l), font=FONT, fill="white")
        def _luma_show_progress(text):
            with canvas(display.device) as draw:
                draw.text((0, 0), str(text), font=FONT_SMALL, fill="white")
        def _luma_clear():
            display.lines = deque(maxlen=display.max_lines)
            with canvas(display.device) as draw:
                pass
        # attach
        display.max_lines = max_lines
        display.lines = deque(maxlen=max_lines)
        display.append_line = _luma_append_line
        display.show_lines = _luma_show_lines
        display.show_progress = _luma_show_progress
        display.clear = _luma_clear
except Exception:
    pass

try:
    # Dummy display: add append_line to print lines and keep buffer
    if isinstance(display, object) and not hasattr(display, 'append_line'):
        max_lines = max(1, HEIGHT // 8)
        display._lines = deque(maxlen=max_lines)
        def _dummy_append_line(line):
            display._lines.append(str(line))
            print("[display] " + " | ".join(list(display._lines)), file=sys.stderr)
        def _dummy_show_lines(lines):
            display._lines = deque([str(x) for x in lines], maxlen=max_lines)
            print("[display] " + " | ".join(list(display._lines)), file=sys.stderr)
        display.append_line = _dummy_append_line
        display.show_lines = _dummy_show_lines
except Exception:
    pass


def append_line(line):
    """Append a single line to the display buffer (safe wrapper)."""
    try:
        display.append_line(str(line))
    except Exception:
        try:
            display.show_progress(str(line))
        except Exception:
            pass


def run_cmd_stream(cmd, prefix=None):
    """Run a command, streaming stdout+stderr lines to the display via append_line.
    Returns the process returncode.
    """
    # Friendly DRY_RUN behaviour
    if DRY_RUN:
        print("DRY RUN: " + " ".join(cmd))
        append_line(f"DRY RUN: {prefix or ''} {' '.join(cmd)}")
        return 0

    append_line(f"{prefix or 'Running'}: {' '.join(cmd[:3])} ...")
    import re
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    percent_re = re.compile(r'(\d{1,3})%')
    upload_success = False
    try:
        for raw in iter(proc.stdout.readline, ''):
            if raw is None:
                break
            line = raw.rstrip('\n')
            if line:
                if 'Upload successful' in line:
                    upload_success = True
                match = percent_re.search(line)
                if match:
                    show_progress(line)
                else:
                    append_line(line)
    except Exception as e:
        append_line(f"Error: {e}")
    finally:
        try:
            if proc.stdout:
                proc.stdout.close()
        except Exception:
            pass
    rc = proc.wait()
    append_line(f"Exit {rc}")
    # Prefer upload_success if detected
    if upload_success:
        return 0
    return rc
