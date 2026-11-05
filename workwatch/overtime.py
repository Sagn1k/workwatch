"""Shared overtime tracking loop used by both foreground and daemon modes.

After the scheduled countdown completes, instead of sleeping the Mac
immediately, keep tracking hours as long as the user remains active on
the machine. When the user has been idle longer than
`inactive_threshold_minutes`, return the last-active timestamp as the
effective exit time for the day.

Suspend handling: macOS `HIDIdleTime` resets on wake, so if the system
was asleep for hours and the user opens the lid the next morning, a
naive `now - idle` would advance `last_active` to "just now". We guard
against that by watching the wall-clock gap between polls — a gap far
larger than `poll_interval` means the process was suspended, and if that
gap alone exceeds the inactivity threshold we end the day at the
pre-suspend `last_active` instead of trusting the post-wake HID value.
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
    # Any wall-clock gap noticeably larger than one poll is evidence the
    # system was suspended between ticks. We only *act* on a gap that
    # also exceeds the inactivity threshold, but we use this smaller
    # value to decide whether to trust `now - idle` on the post-wake
    # poll — after a suspend, HIDIdleTime has been reset and cannot
    # vouch for the stretch of time we were frozen through.
    suspend_hint_seconds = max(poll_interval * 3, 90.0)
    last_active = scheduled_sleep
    last_poll_wall = datetime.now()

    try:
        while True:
            now = datetime.now()
            wall_gap = (now - last_poll_wall).total_seconds()
            last_poll_wall = now

            if wall_gap >= threshold_seconds:
                if on_tick:
                    on_tick(last_active, wall_gap)
                return last_active

            idle = seconds_since_last_activity()

            if idle < threshold_seconds:
                if wall_gap < suspend_hint_seconds:
                    candidate = now - timedelta(seconds=idle)
                    if candidate > last_active:
                        last_active = candidate
                if on_tick:
                    on_tick(last_active, idle)
                time.sleep(poll_interval)
                continue

            if on_tick:
                on_tick(last_active, idle)
            return last_active
    except KeyboardInterrupt:
        if on_interrupt:
            on_interrupt(last_active)
        return last_active
