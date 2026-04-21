"""Monthly attendance archiver.

Emails a month's attendance records (rendered as an HTML summary with
color-coded analytics and a daily table) through the user's Mail.app
account, writes a local backup under ~/.workwatch_archives/, and then
removes the archived entries from ~/.workwatch_history.json to keep the
live history file small.

Trigger manually via `workwatch archive [--month YYYY-MM] [--email ...]`,
or schedule monthly via cron / launchd.
"""

import json
import os
import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path

from workwatch.config import load_history, save_history

ARCHIVE_DIR = Path.home() / ".workwatch_archives"

# Shared color palette for HTML "badges" and plain-text emoji mapping.
# levels:  good | bad | warn | info | primary | neutral
_HTML_BADGE = {
    "good":    ("#0a5c1a", "#ddf4dc"),
    "bad":     ("#9e1414", "#fde8e8"),
    "warn":    ("#7a5b00", "#fff3cd"),
    "info":    ("#0b5cad", "#e2ecf7"),
    "primary": ("#1b1b1b", "#eef1f5"),
    "neutral": ("#555555", "#f2f2f2"),
}
_EMOJI = {
    "good": "🟢",
    "bad":  "🔴",
    "warn": "🟡",
    "info": "🔵",
    "primary": "⭐",
    "neutral": "⚪",
}


def previous_month(today: date | None = None) -> tuple[int, int]:
    """Return (year, month) of the month immediately before `today`."""
    today = today or date.today()
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


def _month_keys(year: int, month: int, history: dict) -> list[str]:
    prefix = f"{year:04d}-{month:02d}-"
    return sorted(k for k in history if k.startswith(prefix))


def _day_row(date_key: str, rec: dict) -> dict:
    """Normalise one history record into a row used by both renderers."""
    hours = float(rec.get("hours_worked") or 0)
    if hours >= 9:
        status_label, level = ("Full", "good")
    elif hours < 5:
        status_label, level = ("Half", "bad")
    else:
        status_label, level = ("Short", "warn")

    d = datetime.strptime(date_key, "%Y-%m-%d").date()
    return {
        "date": date_key,
        "day": d.strftime("%a"),
        "entry": rec.get("entry_time", "—"),
        "exit": rec.get("exit_time", "—"),
        "hours": hours,
        "status_label": status_label,
        "level": level,
        "overtime": max(0.0, hours - 9),
    }


def build_analytics(year: int, month: int, records: dict) -> list[dict]:
    """Return a list of analytics rows suitable for both HTML and plain-text
    rendering. Each row is {label, value, level} where level drives color.
    """
    if not records:
        return [{
            "label": "No records",
            "value": f"nothing logged for {year:04d}-{month:02d}",
            "level": "neutral",
        }]

    hours = [(k, float(v.get("hours_worked") or 0)) for k, v in records.items()]
    total = sum(h for _, h in hours)
    days = len(hours)
    avg = total / days if days else 0.0
    longest = max(hours, key=lambda kv: kv[1])
    shortest = min(hours, key=lambda kv: kv[1])
    ot_days = [(k, h) for k, h in hours if h > 9]
    total_ot = sum(max(0.0, h - 9) for _, h in hours)
    short_days = [(k, h) for k, h in hours if h < 5]

    return [
        {"label": "Month",              "value": f"{year:04d}-{month:02d}",                       "level": "info"},
        {"label": "Working days",       "value": f"{days}",                                        "level": "info"},
        {"label": "Total hours",        "value": f"{total:.2f} h",                                 "level": "primary"},
        {"label": "Average / day",      "value": f"{avg:.2f} h",                                   "level": ("good" if avg >= 9 else ("warn" if avg >= 5 else "bad"))},
        {"label": "Longest day",        "value": f"{longest[0]} — {longest[1]:.2f} h",             "level": "good"},
        {"label": "Shortest day",       "value": f"{shortest[0]} — {shortest[1]:.2f} h",           "level": ("bad" if shortest[1] < 5 else "warn")},
        {"label": "Overtime days (>9h)","value": f"{len(ot_days)} — total {total_ot:.2f} h",       "level": ("primary" if ot_days else "neutral")},
        {"label": "Short / half (<5h)", "value": f"{len(short_days)}",                             "level": ("warn" if short_days else "good")},
    ]


# ---------- HTML body ----------

def _html_badge(text: str, level: str) -> str:
    fg, bg = _HTML_BADGE.get(level, _HTML_BADGE["neutral"])
    return (
        f'<span style="display:inline-block;background:{bg};color:{fg};'
        f'font-weight:600;padding:3px 10px;border-radius:12px;font-size:13px;">'
        f'{text}</span>'
    )


def _build_html_body(year: int, month: int, records: dict,
                     analytics: list[dict]) -> str:
    rows = [_day_row(k, v) for k, v in records.items()]
    month_name = datetime(year, month, 1).strftime("%B %Y")

    analytics_html = []
    for a in analytics:
        analytics_html.append(
            '<tr>'
            f'<td style="padding:10px 14px;color:#555;border-bottom:1px solid #eef1f5;">'
            f'{a["label"]}</td>'
            f'<td style="padding:10px 14px;border-bottom:1px solid #eef1f5;">'
            f'{_html_badge(a["value"], a["level"])}</td>'
            '</tr>'
        )

    table_rows = []
    for r in rows:
        fg, _ = _HTML_BADGE[r["level"]]
        hours_cell = f'{r["hours"]:.2f}'
        if r["overtime"] > 0:
            hours_cell += f' <span style="color:#5e2ba6;font-size:12px;">(+{r["overtime"]:.2f} OT)</span>'
        table_rows.append(
            '<tr>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eef1f5;">{r["date"]}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eef1f5;color:#888;">{r["day"]}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eef1f5;">{r["entry"]}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eef1f5;">{r["exit"]}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eef1f5;text-align:right;'
            f'font-weight:600;color:{fg};">{hours_cell}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eef1f5;">'
            f'{_html_badge(r["status_label"], r["level"])}</td>'
            '</tr>'
        )

    return f'''<!DOCTYPE html><html><body style="margin:0;padding:24px;background:#f6f8fb;
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#1b1b1b;">
<div style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:12px;
padding:28px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
  <h2 style="margin:0 0 4px 0;color:#0b5cad;font-size:22px;">📊 WorkWatch Attendance</h2>
  <div style="color:#888;font-size:14px;margin-bottom:24px;">Monthly archive · {month_name}</div>

  <h3 style="margin:0 0 10px 0;font-size:15px;color:#333;
letter-spacing:0.04em;text-transform:uppercase;">At a glance</h3>
  <table style="border-collapse:collapse;width:100%;margin-bottom:28px;">
    {''.join(analytics_html)}
  </table>

  <h3 style="margin:0 0 10px 0;font-size:15px;color:#333;
letter-spacing:0.04em;text-transform:uppercase;">Daily log ({len(rows)} days)</h3>
  <table style="border-collapse:collapse;width:100%;font-size:14px;">
    <thead>
      <tr style="background:#f0f3f7;color:#333;">
        <th style="padding:10px 12px;text-align:left;border-bottom:1px solid #dde2ea;">Date</th>
        <th style="padding:10px 12px;text-align:left;border-bottom:1px solid #dde2ea;">Day</th>
        <th style="padding:10px 12px;text-align:left;border-bottom:1px solid #dde2ea;">Entry</th>
        <th style="padding:10px 12px;text-align:left;border-bottom:1px solid #dde2ea;">Exit</th>
        <th style="padding:10px 12px;text-align:right;border-bottom:1px solid #dde2ea;">Hours</th>
        <th style="padding:10px 12px;text-align:left;border-bottom:1px solid #dde2ea;">Status</th>
      </tr>
    </thead>
    <tbody>{''.join(table_rows)}</tbody>
  </table>

  <p style="color:#aaa;font-size:12px;margin-top:28px;text-align:center;">
    🤖 Auto-generated by WorkWatch
  </p>
</div>
</body></html>'''


# ---------- Plain-text body (fallback & inbox preview) ----------

def _build_plain_body(year: int, month: int, records: dict,
                      analytics: list[dict]) -> str:
    month_name = datetime(year, month, 1).strftime("%B %Y")
    rows = [_day_row(k, v) for k, v in records.items()]

    lines = [
        f"📊 WorkWatch Attendance — {month_name}",
        "=" * 50,
        "",
        "AT A GLANCE",
        "-" * 50,
    ]
    for a in analytics:
        emoji = _EMOJI.get(a["level"], "•")
        lines.append(f"  {emoji}  {a['label']:<22} {a['value']}")

    lines += [
        "",
        f"DAILY LOG ({len(rows)} days)",
        "-" * 50,
        "  Date        Day   Entry         Exit          Hours    OT     Status",
        "  ──────────  ───   ───────────   ───────────   ──────   ────   ────────",
    ]
    for r in rows:
        ot_str = f"+{r['overtime']:.2f}" if r["overtime"] > 0 else "—"
        emoji = _EMOJI.get(r["level"], "•")
        lines.append(
            f"  {r['date']}  {r['day']:<3}   "
            f"{r['entry']:<11}   {r['exit']:<11}   "
            f"{r['hours']:>5.2f}    {ot_str:<5}  {emoji} {r['status_label']}"
        )

    lines += [
        "",
        "─" * 50,
        "🤖 Auto-generated by WorkWatch",
    ]
    return "\n".join(lines)


# ---------- Mail.app sender ----------

def _send_via_mail_app(to_email: str, subject: str,
                       html_body: str, plain_body: str) -> tuple[bool, str]:
    """Send via Mail.app. Attempts HTML first (via the `html content`
    property which modern Mail.app accepts even though it is not in the
    public scripting dictionary); falls back to plain text if rejected.

    HTML and plain bodies are written to temp files so AppleScript reads
    them with no escaping — immune to quotes, braces, newlines.
    """
    def _write_tmp(content: str, suffix: str) -> str:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=suffix, encoding="utf-8",
        ) as f:
            f.write(content)
            return f.name

    html_path = _write_tmp(html_body, ".html")
    plain_path = _write_tmp(plain_body, ".txt")

    safe_subject = subject.replace('"', "'").replace("\n", " ")
    safe_to = to_email.replace('"', "").strip()

    script = f'''
set htmlText to (read POSIX file "{html_path}" as «class utf8»)
set plainText to (read POSIX file "{plain_path}" as «class utf8»)
tell application "Mail"
  set newMsg to make new outgoing message with properties {{subject:"{safe_subject}", content:plainText, visible:false}}
  tell newMsg
    make new to recipient at end of to recipients with properties {{address:"{safe_to}"}}
  end tell
  try
    -- Modern Mail.app accepts html content even though it's not documented
    set html content of newMsg to htmlText
  end try
  send newMsg
end tell
'''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return False, "osascript timed out"
    except Exception as exc:
        return False, str(exc)
    finally:
        for p in (html_path, plain_path):
            try:
                os.unlink(p)
            except OSError:
                pass

    if result.returncode != 0:
        return False, result.stderr.strip() or "osascript failed"
    return True, "sent"


# ---------- Local backup ----------

def _write_local_backup(year: int, month: int, records: dict,
                        analytics: list[dict], html_body: str) -> Path:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    json_path = ARCHIVE_DIR / f"{year:04d}-{month:02d}.json"
    html_path = ARCHIVE_DIR / f"{year:04d}-{month:02d}.html"

    json_path.write_text(json.dumps(
        {"month": f"{year:04d}-{month:02d}",
         "analytics": analytics, "records": records},
        indent=2, sort_keys=True,
    ) + "\n")
    html_path.write_text(html_body)
    return json_path


# ---------- Orchestrator ----------

def archive_month(
    year: int, month: int, to_email: str, dry_run: bool = False,
) -> tuple[bool, str]:
    """Email and delete records for the given month.

    Order of operations (to avoid data loss):
      1. Filter history to the month's records.
      2. Write a local backup under ~/.workwatch_archives/ (JSON + HTML).
      3. Send the email via Mail.app.
      4. Only on send success: remove those dates from history.

    Returns (ok, message). For dry_run, nothing is persisted or sent;
    the returned `message` is the plain-text preview of the email.
    """
    history = load_history()
    keys = _month_keys(year, month, history)
    if not keys:
        return False, f"No records found for {year:04d}-{month:02d}"

    records = {k: history[k] for k in keys}
    analytics = build_analytics(year, month, records)
    html_body = _build_html_body(year, month, records, analytics)
    plain_body = _build_plain_body(year, month, records, analytics)
    subject = f"WorkWatch Attendance — {year:04d}-{month:02d} ({len(keys)} days)"

    if dry_run:
        return True, plain_body

    backup_path = _write_local_backup(year, month, records, analytics, html_body)

    ok, msg = _send_via_mail_app(to_email, subject, html_body, plain_body)
    if not ok:
        return False, f"send failed ({msg}); backup kept at {backup_path}"

    for k in keys:
        history.pop(k, None)
    save_history(history)

    return True, (
        f"archived {len(keys)} day(s) for {year:04d}-{month:02d} to {to_email} "
        f"(local backup: {backup_path})"
    )
