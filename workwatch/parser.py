"""Email body parsing for VMock attendance entries."""

import re
from datetime import datetime
from typing import Optional


ENTRY_PATTERN = re.compile(
    r"Entry Allowed.*?on\s+\d{2}/\d{2}/\d{4}\s+(\d{1,2}:\d{2}:\d{2}\s*[APap][Mm])"
)


def parse_entry_times(email_bodies: list[str]) -> list[datetime]:
    """Extract all entry times from a list of email body strings.

    Returns a sorted list of datetime objects (earliest first).
    """
    today = datetime.now().date()
    times = []

    for body in email_bodies:
        for match in ENTRY_PATTERN.finditer(body):
            time_str = match.group(1).strip()
            try:
                t = datetime.strptime(time_str, "%I:%M:%S %p")
                entry_dt = datetime.combine(today, t.time())
                times.append(entry_dt)
            except ValueError:
                continue

    times.sort()
    return times


def get_earliest_entry(email_bodies: list[str]) -> Optional[datetime]:
    """Return the earliest entry time from today's attendance emails."""
    times = parse_entry_times(email_bodies)
    return times[0] if times else None
