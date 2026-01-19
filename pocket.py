# VK3MBT Pocket Programmer. Not for commercial use.
# OLED Version to select named images to upload

# ..adjust PROFILES [ ] array to suit your needs
# In this example, colour names are used...
# Green, Yellow, Blue, Red, Pink,Cyan, Purple
# Button 1 - Select Colour
# Button 2 - Upload selected colour named image and the connected radio
# Button 3 - Download from Radio (will save to selected colour's radio folder)
# Long press Button 3 - Shutdown Pi

from signal import pause
from time import sleep
import time
import RPi.GPIO as GPIO
import os
import subprocess
import re
import threading
from display import show_selected, show_status, show_progress, clear, close as close_display, run_cmd_stream, show_report

# Small startup message on display (if available)
try:
    show_status("Starting...")
except Exception:
    pass

# Available colours: (name, rgb tuple, filename, radio model)
PROFILES = [
    ("green",  (0, 1, 0), "green.img","QYT_KT-WP12"),
    ("yellow", (1, 0.3, 0), "yellow.img","QYT_KT-WP12"),
    ("blue",   (0, 0.1, 1), "blue.img","QYT_KT-WP12"),
    ("red",    (1, 0, 0), "red.img","QYT_KT-WP12"),
    ("pink",   (1, 0.1, 0.1), "pink.img","Baofeng_UV-5R"),
    ("cyan",   (0, 1, 1), "cyan.img","Baofeng_UV-5R"),
    ("purple", (0.3, 0, 1), "purple.img","Baofeng_UV-5R"),
]
SELECTED_INDEX = 0
selected_colour = PROFILES[SELECTED_INDEX][0]

# Dry run support via POCKET_DRY_RUN (useful when developing off-device)
DRY_RUN = os.getenv("POCKET_DRY_RUN", "").lower() in ("1", "true", "yes")

# Set initial display to match the selected colour
try:
    show_selected(PROFILES[SELECTED_INDEX][0], PROFILES[SELECTED_INDEX][2], PROFILES[SELECTED_INDEX][3])
except Exception:
    pass

SELECT_PIN = 13
WRITE_PIN = 19
READ_PIN = 26
LONG_PRESS_SEC = 2.0
# DOUBLE_PRESS_WINDOW = 0.6

_press_start = 0.0
# _last_press = 0.0

GPIO.setmode(GPIO.BCM)
GPIO.setup(SELECT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(WRITE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(READ_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def _next_incremental_filename(path):
    """Return next available numbered filename alongside path (download1.img, download2.img, ...)."""
    d = os.path.dirname(path) or '.'
    base = os.path.basename(path)
    name, ext = os.path.splitext(base)
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    pat = re.compile(re.escape(name) + r"(\d+)" + re.escape(ext) + r"\Z")
    maxn = 0
    for f in os.listdir(d):
        m = pat.match(f)
        if m:
            try:
                n = int(m.group(1))
                if n > maxn:
                    maxn = n
            except ValueError:
                pass
    nextn = maxn + 1
    return os.path.join(d, f"{name}{nextn}{ext}")


def select():
    """Cycle the selected colour and update the LED."""
    global SELECTED_INDEX, selected_colour
    SELECTED_INDEX = (SELECTED_INDEX + 1) % len(PROFILES)
    name, rgb, fname, radio = PROFILES[SELECTED_INDEX]
    selected_colour = name
    directory =  radio
    print(f"Button 1 Select colour pressed. Selected: {name}")
    try:
        show_selected(name, fname, radio)
    except Exception:
        pass
    print("Waiting for button press...")

def write():
    """Upload the currently selected colour's image."""
    name, rgb, fname, radio = PROFILES[SELECTED_INDEX]
    directory = radio 
    print(f"Button 2 pressed. Uploading {radio} {fname} (selected={name})")
    # indicate running on display
    show_report("Uploading",fname, radio)
    cmd = ["chirpc", "-r", f"{radio}", "--serial=/dev/ttyUSB0", f"--mmap=/home/pi/Radios/{directory}/{fname}", "--upload-mmap"]
    try:
        import subprocess
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        output, _ = proc.communicate()
        rc = proc.returncode
        success = (rc == 0) or (output and ("Upload successful" in output or "Success" in output))
    except Exception:
        success = False
    clear()
    if not success:
        show_status("Upload complete")
        show_selected(name, fname, radio)
    else:
        show_status("Upload complete")
        show_selected(name, fname, radio)
    print("Waiting for button press...")
def read():
    print("Button 3 pressed. Downloading from Radio.")
    name, rgb, fname, radio = PROFILES[SELECTED_INDEX]
    base_mmap = f"/home/pi/Radios/{radio}/download.img"
    target_mmap = _next_incremental_filename(base_mmap)
    print(f"Saving download to {target_mmap}")
    # show_status(f"Downloading.")
    show_report("Downloading","download[n]", radio)
    cmd = ["chirpc", "-r", f"{radio}", "--serial=/dev/ttyUSB0", f"--mmap={target_mmap}", "--download-mmap"]
    try:
        import subprocess
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        output, _ = proc.communicate()
        # Detect '100.0%' in output as success
        success = output and '100.0%' in output
    except Exception as e:
        print(f"[DEBUG] Download exception: {e}")
        success = False
    clear()
    if success:
        show_status(f"Saved to {target_mmap}")
        show_selected(name, fname, radio)
    else:
        show_status("Download complete")
        show_selected(name, fname, radio)
    print("Waiting for button press...")

def shutdown_pi():
        print("Long press detected: shutting down")
        try:
            show_status("Shutting down...")
        except Exception:
            pass
        subprocess.run(["sudo", "shutdown", "-h", "now"])

def _on_read_edge(channel):
        """Handle both edges for read button to detect long press."""
        global _press_start
        now = time.time()
        if GPIO.input(channel) == GPIO.LOW:
            _press_start = now
            return
        duration = now - _press_start
        if duration >= LONG_PRESS_SEC:
            shutdown_pi()
            return
        read()
# Main loop to wait for button presses

# Try using GPIO event detection; if it fails (permissions/driver issue), fall back to polling
EVENT_DETECT_AVAILABLE = True

try:
    GPIO.add_event_detect(READ_PIN, GPIO.BOTH, callback=_on_read_edge, bouncetime=50)
    GPIO.add_event_detect(SELECT_PIN, GPIO.FALLING, callback=lambda x: select(), bouncetime=300)
    GPIO.add_event_detect(WRITE_PIN, GPIO.FALLING, callback=lambda x: write(), bouncetime=300)
except Exception as e:
    EVENT_DETECT_AVAILABLE = False
    # print(f"Warning: GPIO event detect unavailable ({e}); using polling fallback")

    def _polling_loop():
        # Simple, debounced polling loop that detects falling edges and long-press on READ_PIN
        last_read_state = GPIO.input(READ_PIN)
        last_select_state = GPIO.input(SELECT_PIN)
        last_write_state = GPIO.input(WRITE_PIN)
        read_press_start = None
        while True:
            try:
                time.sleep(0.05)
                # READ button: detect press/release for long-press behaviour
                rs = GPIO.input(READ_PIN)
                if rs == GPIO.LOW and last_read_state != GPIO.LOW:
                    # pressed down
                    read_press_start = time.time()
                if rs != GPIO.LOW and last_read_state == GPIO.LOW:
                    # released
                    if read_press_start is not None:
                        duration = time.time() - read_press_start
                        if duration >= LONG_PRESS_SEC:
                            try:
                                shutdown_pi()
                            except Exception:
                                pass
                        else:
                            try:
                                read()
                            except Exception:
                                pass
                    read_press_start = None
                last_read_state = rs
                # SELECT button: falling edge
                ss = GPIO.input(SELECT_PIN)
                if ss == GPIO.LOW and last_select_state != GPIO.LOW:
                    try:
                        select()
                    except Exception:
                        pass
                last_select_state = ss
                # WRITE button: falling edge
                ws = GPIO.input(WRITE_PIN)
                if ws == GPIO.LOW and last_write_state != GPIO.LOW:
                    try:
                        write()
                    except Exception:
                        pass
                last_write_state = ws
            except Exception:
                # If something goes wrong (eg. FakeGPIO), yield briefly and continue
                time.sleep(0.2)

    t = threading.Thread(target=_polling_loop, daemon=True)
    t.start()

print(">>>> Pocket OLED is ready..   2601191326") 
print("Waiting for button press...")
show_report("Pocket: CHIRP","1-Select", "2-Upld 3-Dwnld")
sleep(5)
name, rgb, fname, radio = PROFILES[0]
show_selected(name, fname, radio)

try:
    pause()  # wait indefinitely until signal (callbacks will run)
except KeyboardInterrupt:
    print("Exiting on user interrupt...")
finally:
    try:
        close_display()
    except Exception:
        pass
    GPIO.cleanup()
