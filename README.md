# WorkWatch

Auto-sleep your Mac after your work hours are done. Connects to Apple Mail.app to find your VMock attendance email, parses entry time, and puts the laptop to sleep after the configured work hours.

## Prerequisites

- **macOS** (requires Mail.app and `pmset`)
- Gmail account added to **Apple Mail** (System Settings → Internet Accounts)
- Mail.app running and synced before launching WorkWatch
- Python 3.9+ (only needed for source install — the binary has no dependencies)

## Installation

### Option 1: One-line Install (Binary)

```bash
curl -fsSL https://sagnikbhowmick.com/workwatch/install.sh | bash
```

This downloads a prebuilt binary to `/usr/local/bin`. To use a custom directory:

```bash
WORKWATCH_INSTALL_DIR=~/.local/bin curl -fsSL https://sagnikbhowmick.com/workwatch/install.sh | bash
```

### Option 2: Install from Source

```bash
git clone https://github.com/sagnikb7/workwatch.git
cd workwatch
pip install -e .
```

This installs `workwatch` as a Python package. Any edits to the source take effect immediately.

### Option 3: Build Binary Locally

```bash
git clone https://github.com/sagnikb7/workwatch.git
cd workwatch
make build
sudo cp dist/workwatch /usr/local/bin/
```

### Verify Installation

```bash
workwatch version
# WorkWatch v1.0.0
```

## Usage

### Foreground Mode (Live Countdown)

```bash
workwatch
```

1. Queries Mail.app for today's attendance email from the configured sender
2. Parses the earliest "Entry Allowed" timestamp
3. Shows a live countdown timer in the terminal
4. When it hits zero, saves the record and puts your Mac to sleep

If no email is found yet, it retries automatically every 5 minutes.

### Background Mode (Daemon)

```bash
workwatch --bg
```

Runs silently in the background — you can close the terminal. Sends macOS notifications for:
- Email found / countdown started
- 5-minute warning before sleep
- Putting Mac to sleep

Manage the daemon:

```bash
workwatch status       # Check if daemon is running
workwatch stop         # Stop the daemon
```

Daemon logs: `~/.workwatch.log` | PID file: `~/.workwatch.pid`

### Monthly Attendance Log

```bash
workwatch log                    # Current month
workwatch log --month 2026-02    # Specific month
```

Color-coded table with entry/exit times, hours worked, and monthly summary:
- 🟢 Green — 9+ hours (done)
- 🟡 Yellow — In progress (today)
- 🔴 Red — Under 9 hours (short)
- ⚪ Gray — Weekend / no data

### All Commands

| Command | Description |
|---|---|
| `workwatch` | Start foreground countdown timer |
| `workwatch --bg` | Start background daemon |
| `workwatch status` | Check daemon status |
| `workwatch stop` | Stop background daemon |
| `workwatch log` | Show monthly attendance log |
| `workwatch log --month YYYY-MM` | Show log for a specific month |
| `workwatch version` | Print version |
| `workwatch help` | Show help text |

## Configuration

Config file: `~/.workwatch.json` (auto-created on first run)

```json
{
  "work_hours": 9,
  "sender": "attendance@vmock.com"
}
```

| Key | Description | Default |
|---|---|---|
| `work_hours` | Hours to work before sleep (supports decimals like `8.5`) | `9` |
| `sender` | Email address to search for in Mail.app | `attendance@vmock.com` |

## Files

| Path | Purpose |
|---|---|
| `~/.workwatch.json` | Configuration (work hours, sender) |
| `~/.workwatch_history.json` | Attendance records (auto-managed) |
| `~/.workwatch.log` | Daemon log (background mode only) |
| `~/.workwatch.pid` | Daemon PID (background mode only) |

## Building & Releasing

### Build Commands

```bash
make build       # Build standalone binary → dist/workwatch
make install     # Build + copy to /usr/local/bin
make release     # Build + create tarball + SHA-256 checksum
make dev         # pip install -e . (editable source install)
make run         # Run directly from source
make run-log     # Run log view from source
make clean       # Remove build artifacts
```

### Creating a Release

```bash
make release
```

This produces:
```
release/
├── workwatch-1.0.0-darwin-arm64.tar.gz
└── workwatch-1.0.0-darwin-arm64.tar.gz.sha256
```

### Deploying to Your Server

Upload the release artifacts and install script to your web server:

```bash
scp release/* your-server:/var/www/sagnikbhowmick.com/workwatch/releases/
scp scripts/install.sh your-server:/var/www/sagnikbhowmick.com/workwatch/install.sh
```

Then anyone on a Mac can install with:
```bash
curl -fsSL https://sagnikbhowmick.com/workwatch/install.sh | bash
```

The installer auto-detects architecture (arm64/x86_64), verifies SHA-256 checksums, and falls back to source install via pip if the binary download fails.

## Project Structure

```
workwatch/
├── Makefile                  # Build, install, release targets
├── pyproject.toml            # Python package config
├── workwatch.spec            # PyInstaller binary spec
├── scripts/
│   ├── install.sh            # Remote installer (curl | bash)
│   └── release.sh            # Build + package release artifacts
└── workwatch/
    ├── __init__.py            # Package version
    ├── __main__.py            # python -m workwatch support
    ├── cli.py                 # CLI entry point & command routing
    ├── config.py              # Config & history file management
    ├── daemon.py              # Background mode (fork, notifications, PID)
    ├── log_display.py         # ANSI color-coded monthly table
    ├── mail_reader.py         # AppleScript ↔ Mail.app integration
    ├── parser.py              # Regex extraction of entry times
    └── timer.py               # Live countdown display
```

## How It Works

1. Queries Apple Mail.app via AppleScript for today's emails from the configured sender
2. Filters by today's date natively in Mail.app for fast lookups
3. Parses "Entry Allowed" timestamps from email bodies using regex
4. If multiple entry emails exist, uses the earliest (first check-in)
5. Calculates sleep time = earliest entry + configured work hours
6. Foreground: live terminal countdown | Background: silent daemon with macOS notifications
7. When countdown hits zero, saves attendance record to `~/.workwatch_history.json`
8. Triggers `pmset sleepnow` to put the Mac to sleep

## License

MIT
