# WorkWatch

Auto-sleep your Mac after your work hours are done. Connects to Apple Mail.app to find your VMock attendance email, parses entry time, and puts the laptop to sleep after the configured work hours.

## Quick Install

```bash
curl -fsSL https://sagnikbhowmick.com/workwatch/install.sh | bash
```

Or set a custom install directory:

```bash
WORKWATCH_INSTALL_DIR=~/.local/bin curl -fsSL https://sagnikbhowmick.com/workwatch/install.sh | bash
```

## Prerequisites

- **macOS** (requires Mail.app and `pmset`)
- Gmail account added to Apple Mail (System Settings → Internet Accounts)
- Mail.app running and synced

## Usage

### Start countdown timer

```bash
workwatch
```

Finds today's attendance email, parses your entry time, and starts a live countdown. When time's up, your Mac goes to sleep.

### View monthly attendance log

```bash
workwatch log
workwatch log --month 2026-02
```

Color-coded table showing your daily entry/exit times, hours worked, and monthly summary.

### Other commands

```bash
workwatch help       # Show help
workwatch version    # Show version
```

## Configuration

Config file: `~/.workwatch.json` (auto-created on first run)

```json
{
  "work_hours": 9,
  "sender": "attendance@vmock.com"
}
```

- `work_hours` — Hours to work before sleep (supports decimals like `8.5`)
- `sender` — Email address to search for in Mail.app

## History

Attendance records are stored in `~/.workwatch_history.json` (auto-managed).

## Install from Source

```bash
git clone https://github.com/sagnikb7/workwatch.git
cd workwatch
pip install -e .
workwatch
```

## Build Binary

```bash
make build       # Build standalone binary
make install     # Build and install to /usr/local/bin
make release     # Build + create release tarball
```

## Deploy to Your Server

After running `make release`:

```bash
scp release/* your-server:/var/www/sagnikbhowmick.com/workwatch/releases/
scp scripts/install.sh your-server:/var/www/sagnikbhowmick.com/workwatch/install.sh
```

## How It Works

1. Queries Apple Mail.app via AppleScript for today's emails from the configured sender
2. Parses "Entry Allowed" timestamps from email bodies
3. Calculates sleep time = earliest entry + configured work hours
4. Displays a live countdown timer in your terminal
5. When countdown hits zero, saves the attendance record and runs `pmset sleepnow`

## License

MIT
