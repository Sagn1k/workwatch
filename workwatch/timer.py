"""Live countdown timer display for WorkWatch."""

import os
import sys
import time
from datetime import datetime, timedelta

VERSION = "1.0.0"


def clear_screen():
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def format_time_12h(dt: datetime) -> str:
    """Format datetime as HH:MM:SS AM/PM."""
    return dt.strftime("%I:%M:%S %p")


def format_duration(seconds: int) -> str:
    """Format seconds as HH:MM:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def render_header(entry_time: datetime, sleep_time: datetime):
    """Render the static header portion of the display."""
    today_str = datetime.now().strftime("%d/%m/%Y")
    entry_str = format_time_12h(entry_time)
    sleep_str = format_time_12h(sleep_time)

    print(f"\033[1;36m╔══════════════════════════════════════════╗\033[0m")
    print(f"\033[1;36m║\033[0m          \033[1;37m⏱  WorkWatch v{VERSION}\033[0m              \033[1;36m║\033[0m")
    print(f"\033[1;36m║\033[0m   \033[0;37mAuto-sleep after your work hours\033[0m       \033[1;36m║\033[0m")
    print(f"\033[1;36m╚══════════════════════════════════════════╝\033[0m")
    print()
    print(f"  📅 Date:       \033[1;37m{today_str}\033[0m")
    print(f"  🕐 Entry Time: \033[1;32m{entry_str}\033[0m")
    print(f"  🛑 Sleep At:   \033[1;31m{sleep_str}\033[0m")
    print(f"  \033[0;90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print()


def render_countdown(remaining_seconds: int):
    """Render the countdown portion."""
    time_str = format_duration(remaining_seconds)

    if remaining_seconds <= 300:  # Last 5 minutes - red
        color = "\033[1;31m"
    elif remaining_seconds <= 1800:  # Last 30 minutes - yellow
        color = "\033[1;33m"
    else:
        color = "\033[1;32m"

    print(f"          \033[1;37m⏳ Time Remaining\033[0m")
    print()
    print(f"             {color}{time_str}\033[0m")
    print()
    print(f"  \033[0;90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print(f"  \033[0;90mPress Ctrl+C to cancel\033[0m")


def run_countdown(entry_time: datetime, sleep_time: datetime) -> bool:
    """Run the live countdown timer.

    Returns True if countdown completed, False if interrupted.
    """
    try:
        while True:
            now = datetime.now()
            remaining = (sleep_time - now).total_seconds()

            if remaining <= 0:
                clear_screen()
                render_header(entry_time, sleep_time)
                print(f"          \033[1;31m⏰ TIME'S UP!\033[0m")
                print()
                print(f"  \033[1;33mPutting your Mac to sleep...\033[0m")
                print()
                return True

            clear_screen()
            render_header(entry_time, sleep_time)
            render_countdown(int(remaining))

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n")
        print(f"  \033[1;33m👋 Countdown cancelled. Keep working!\033[0m")
        print(f"  \033[0;90mNo attendance record saved.\033[0m")
        print()
        return False


def show_waiting(retry_count: int, next_retry: datetime):
    """Show the waiting-for-email screen."""
    clear_screen()
    print(f"\033[1;36m╔══════════════════════════════════════════╗\033[0m")
    print(f"\033[1;36m║\033[0m          \033[1;37m⏱  WorkWatch v{VERSION}\033[0m              \033[1;36m║\033[0m")
    print(f"\033[1;36m║\033[0m   \033[0;37mWaiting for attendance email...\033[0m        \033[1;36m║\033[0m")
    print(f"\033[1;36m╚══════════════════════════════════════════╝\033[0m")
    print()
    print(f"  ⏳ No attendance email found yet.")
    print(f"  🔄 Retry #{retry_count} — Next check at \033[1;37m{format_time_12h(next_retry)}\033[0m")
    print()
    print(f"  \033[0;90mPress Ctrl+C to cancel\033[0m")
