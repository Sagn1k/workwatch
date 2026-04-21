"""macOS user-activity probe via the HID idle counter.

Uses `ioreg -c IOHIDSystem`'s HIDIdleTime field, which is the time in
nanoseconds since the last keyboard or mouse event. No extra dependencies
or permissions required.
"""

import re
import subprocess

_HID_IDLE_RE = re.compile(r'"HIDIdleTime"\s*=\s*(\d+)')


def seconds_since_last_activity() -> float:
    """Return seconds since the last HID (keyboard/mouse) event.

    Returns 0.0 if the probe fails, so a broken probe never falsely
    triggers end-of-day detection.
    """
    try:
        result = subprocess.run(
            ["ioreg", "-c", "IOHIDSystem"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return 0.0

    if result.returncode != 0:
        return 0.0

    match = _HID_IDLE_RE.search(result.stdout)
    if not match:
        return 0.0

    try:
        return int(match.group(1)) / 1_000_000_000
    except ValueError:
        return 0.0
