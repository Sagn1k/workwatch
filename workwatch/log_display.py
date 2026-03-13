"""Monthly attendance log display with ANSI colors and box-drawing."""

import calendar
from datetime import datetime, date
from workwatch.config import load_history


# ANSI color codes
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[0;90m"
    WHITE = "\033[1;37m"
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[1;31m"
    CYAN = "\033[1;36m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_RED = "\033[41m"


def _format_hours(hours: float) -> str:
    """Format decimal hours as Xh Ym."""
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h}h {m:02d}m"


def _get_status(entry: dict, day_date: date, today: date) -> tuple[str, str]:
    """Return (status_text, color) for a history entry."""
    if entry.get("exit_time") is None and day_date == today:
        return "🟡 Active", C.YELLOW
    hours = entry.get("hours_worked", 0)
    if hours >= 9.0:
        return "🟢 Done", C.GREEN
    return "🔴 Short", C.RED


def show_log(year: int = None, month: int = None):
    """Display the monthly attendance log table."""
    today = date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    history = load_history()
    month_name = calendar.month_name[month]
    _, num_days = calendar.monthrange(year, month)

    # Column widths
    W_DATE = 6
    W_DAY = 5
    W_ENTRY = 12
    W_EXIT = 12
    W_HOURS = 11
    W_STATUS = 14
    TOTAL_W = W_DATE + W_DAY + W_ENTRY + W_EXIT + W_HOURS + W_STATUS + 7  # 7 for separators

    def pad(text: str, width: int) -> str:
        """Pad text to width, accounting for emoji width."""
        # Emojis take ~2 display columns but len() counts them as 1-2 chars
        visible_len = len(text)
        # Count emoji characters (rough heuristic)
        emoji_count = sum(1 for ch in text if ord(ch) > 0x1F000)
        adjusted = visible_len + emoji_count
        padding = max(0, width - adjusted)
        return text + " " * padding

    def row(d, day, entry_t, exit_t, hours, status, color=""):
        """Format a single table row."""
        reset = C.RESET if color else ""
        print(
            f"{C.CYAN}║{C.RESET} {color}{pad(d, W_DATE)}{reset}"
            f"{C.CYAN}║{C.RESET} {color}{pad(day, W_DAY)}{reset}"
            f"{C.CYAN}║{C.RESET} {color}{pad(entry_t, W_ENTRY)}{reset}"
            f"{C.CYAN}║{C.RESET} {color}{pad(exit_t, W_EXIT)}{reset}"
            f"{C.CYAN}║{C.RESET} {color}{pad(hours, W_HOURS)}{reset}"
            f"{C.CYAN}║{C.RESET} {color}{pad(status, W_STATUS)}{reset}"
            f"{C.CYAN}║{C.RESET}"
        )

    # Header
    title = f"📊 WorkWatch — {month_name} {year}"
    print(f"{C.CYAN}╔{'═' * TOTAL_W}╗{C.RESET}")
    print(f"{C.CYAN}║{C.RESET} {C.WHITE}{title}{C.RESET}{' ' * (TOTAL_W - len(title) - 1)}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═' * (W_DATE + 1)}╦{'═' * (W_DAY + 1)}╦{'═' * (W_ENTRY + 1)}╦{'═' * (W_EXIT + 1)}╦{'═' * (W_HOURS + 1)}╦{'═' * (W_STATUS + 1)}╣{C.RESET}")

    row("Date", "Day", "Entry Time", "Exit Time", "  Hours", "   Status")

    print(f"{C.CYAN}╠{'═' * (W_DATE + 1)}╬{'═' * (W_DAY + 1)}╬{'═' * (W_ENTRY + 1)}╬{'═' * (W_EXIT + 1)}╬{'═' * (W_HOURS + 1)}╬{'═' * (W_STATUS + 1)}╣{C.RESET}")

    # Data rows
    total_hours = 0.0
    days_worked = 0

    for day_num in range(1, num_days + 1):
        day_date = date(year, month, day_num)
        day_name = calendar.day_abbr[day_date.weekday()]
        date_key = day_date.strftime("%Y-%m-%d")
        day_str = f" {day_num:02d}"

        # Future dates - skip
        if day_date > today:
            continue

        # Weekend
        if day_date.weekday() >= 5:
            row(day_str, day_name, "    —", "    —", "    —", " ⚪ Weekend", C.DIM)
            continue

        # Check history
        if date_key in history:
            entry = history[date_key]
            entry_t = entry.get("entry_time", "—")
            exit_t = entry.get("exit_time", "—") or "—"
            hours = entry.get("hours_worked", 0)
            status_text, color = _get_status(entry, day_date, today)

            hours_str = _format_hours(hours) if hours else "    —"
            if exit_t == "—":
                hours_str = "    —"

            row(day_str, day_name, f" {entry_t}" if entry_t != "—" else "    —",
                f" {exit_t}" if exit_t != "—" else "    —",
                f"  {hours_str}", f" {status_text}", color)

            if hours:
                total_hours += hours
                days_worked += 1
        else:
            # Workday with no data
            if day_date < today:
                row(day_str, day_name, "    —", "    —", "    —", " ⚪ No data", C.DIM)
            else:
                # Today, no entry yet
                row(day_str, day_name, "    —", "    —", "    —", " 🟡 Pending", C.YELLOW)

    # Summary footer
    avg_hours = total_hours / days_worked if days_worked > 0 else 0
    summary = f" 📈 Days Worked: {days_worked} | Avg: {_format_hours(avg_hours)} | Total: {_format_hours(total_hours)}"

    print(f"{C.CYAN}╠{'═' * (W_DATE + 1)}╩{'═' * (W_DAY + 1)}╩{'═' * (W_ENTRY + 1)}╩{'═' * (W_EXIT + 1)}╩{'═' * (W_HOURS + 1)}╩{'═' * (W_STATUS + 1)}╣{C.RESET}")
    print(f"{C.CYAN}║{C.RESET} {C.WHITE}{summary}{C.RESET}{' ' * max(0, TOTAL_W - len(summary) - 1)}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╚{'═' * TOTAL_W}╝{C.RESET}")
