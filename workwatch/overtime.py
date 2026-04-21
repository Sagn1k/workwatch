"""Shared overtime tracking loop used by both foreground and daemon modes.

After the scheduled countdown completes, instead of sleeping the Mac
immediately, keep tracking hours as long as the user remains active on
the machine. When the user has been idle longer than
`inactive_threshold_minutes`, return the last-active timestamp as the
effective exit time for the day.
"""

import time
from datetime import datetime, timedelta
from typing import Callable, Optional

from workwatch.activity import seconds_since_last_activity


def run_overtime_loop(
    entry_time: datetime,
    scheduled_sleep: datetime,
    config: dict,
    poll_interval: float = 30.0,
    on_tick: Optional[Callable[[datetime, float], None]] = None,
    on_interrupt: Optional[Callable[[datetime], None]] = None,
) -> datetime:
    """Poll user activity until idle exceeds the threshold.

    Returns the last-active datetime — i.e. the effective exit time.
    If interrupted by Ctrl+C, returns the most recent last-active value
    (after invoking `on_interrupt` if provided).

    `on_tick(last_active, idle_seconds)` is called each poll while the
    user is still considered active, allowing the foreground timer or
    daemon state file to refresh the UI.
    """
    threshold_seconds = float(config.get("inactive_threshold_minutes", 10)) * 60
    last_active = scheduled_sleep

    try:
        while True:
            idle = seconds_since_last_activity()
            now = datetime.now()

            if idle < threshold_seconds:
                candidate = now - timedelta(seconds=idle)
                if candidate > last_active:
                    last_active = candidate
                if on_tick:
                    on_tick(last_active, idle)
                time.sleep(poll_interval)
                continue

            # Idle threshold exceeded — wrap up.
            if on_tick:
                on_tick(last_active, idle)
            return last_active
    except KeyboardInterrupt:
        if on_interrupt:
            on_interrupt(last_active)
        return last_active
