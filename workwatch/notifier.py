"""macOS notification helper for WorkWatch."""

import subprocess


def notify(title: str, message: str):
    """Send a macOS notification via osascript."""
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_msg = message.replace("\\", "\\\\").replace('"', '\\"')

    script = 'display notification "' + safe_msg + '" with title "' + safe_title + '"'

    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=10,
        )
    except Exception:
        pass
