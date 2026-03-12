# SRT Ticket Automation

[한국어](README.md)

An automated ticket booking system for SRT (Super Rapid Train) that continuously searches for available tickets, auto-reserves the first one found, and notifies you via email, desktop, and Telegram.

## Features

- **Continuous ticket monitoring** with configurable search parameters
- **Multi-column ticket detection**: 일반실 (standard), 예약대기 (waitlist), and optionally 특실 (first class)
- **Auto-login recovery**: Detects session expiry and re-authenticates automatically
- **Multi-channel notifications**: Email (SMTP/AppleScript), desktop (macOS/Linux/Windows), Telegram (via openclaw)
- **CLI flags** for all parameters — no code editing needed
- **Robust error handling** with automatic browser restart and progressive backoff
- **Background-friendly**: Runs without stealing window focus

## Requirements

- **Python 3.12+**
- **macOS**, **Linux**, or **Windows**
- **Chrome browser** with remote debugging enabled
- **uv** package manager
- **terminal-notifier** (macOS only, `brew install terminal-notifier`)
- **openclaw** (optional, for Telegram notifications)

## Installation

```bash
# 1. Install dependencies
uv sync

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your email and SMTP credentials

# 3. Start Chrome in debugging mode (see platform-specific instructions below)
```

### Starting Chrome in Debug Mode

You must start Chrome with the remote debugging port **before** running the automation.
**Close all existing Chrome windows first**, then run:

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

**Linux:**
```bash
google-chrome --remote-debugging-port=9222
# or
/opt/google/chrome/google-chrome --remote-debugging-port=9222
```

**Windows (CMD):**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

**Windows (PowerShell):**
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

> Once Chrome is open, log into the SRT site (https://etk.srail.kr). The automation will use your saved session.

## Usage

### Quick Start (defaults: 동대구 → 수서)

```bash
uv run run_automation.py
```

### With Custom Parameters

```bash
uv run run_automation.py \
  --departure 동대구 \
  --arrival 수서 \
  --date 20260314 \
  --time 080000 \
  --tickets 2
```

### Filter by Max Arrival Time (only trains arriving by 12:00)

```bash
uv run run_automation.py --max-arrival 1200
```

### Include First Class Seats

```bash
uv run run_automation.py --first-class
```

### All Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--departure` | 동대구 | Departure station |
| `--arrival` | 수서 | Arrival station |
| `--date` | 20260314 | Travel date (YYYYMMDD) |
| `--time` | 080000 | Departure time (HHMMSS) |
| `--tickets` | 2 | Number of tickets |
| `--first-class` | off | Also check 특실 (first class) |
| `--max-arrival` | none | Max arrival time (HHMM, e.g. 1200) |
| `--max-restarts` | 5 | Max browser restart attempts |

## How It Works

```
run_automation.py (CLI)
  └─ main() — outer retry loop (up to 5 restarts)
      └─ run_ticket_search()
          ├─ Launch browser via CDP (localhost:9222)
          ├─ Navigate to SRT booking page
          ├─ Fill form (departure, arrival, date, time, tickets)
          └─ continuous_ticket_search() — polling loop
              ├─ Check session health (auto re-login if expired)
              ├─ Click search button
              ├─ Check results: 일반실 → 예약대기 → 특실
              │   ├─ Found → click 예약하기, notify, exit
              │   └─ Not found → refill form, repeat
              └─ On 5 consecutive errors → restart browser
```

### Ticket Detection Priority

1. **일반실** (standard, td[7]) — always checked
2. **예약대기** (waitlist, td[8]) — always checked
3. **특실** (first class, td[6]) — only with `--first-class`

Clicks the first `예약하기` link found in priority order.

### Session Recovery

The automation detects three page states:
- **Logged in on search page** → continue normally
- **Not logged in** → navigate to login page, click 로그인 (Chrome has saved credentials), return to search
- **Unknown page** → navigate back to search page and refill form

## Notifications

When a ticket is found, all three fire simultaneously:

| Channel | Method | Platform |
|---------|--------|----------|
| Email | SMTP (default) → AppleScript (macOS fallback) | All |
| Desktop | terminal-notifier (macOS) / desktop-notifier (Linux/Windows) | All |
| Telegram | openclaw (optional) | All |

Email settings are managed in the `.env` file. See `.env.example` for reference.

## Project Structure

```
automate-ticketing-srt/
├── main.py                 # Core automation logic
├── run_automation.py       # CLI entry point
├── notification.py         # Desktop notifications (cross-platform)
├── send_email_smtp.py      # Email via SMTP (cross-platform)
├── send_email.py           # Email via AppleScript (macOS fallback)
├── send_imessage.py        # iMessage notifications (macOS only)
├── .env.example            # Environment variable template
└── pyproject.toml          # Dependencies
```

## Logging

- **Console**: Clean, minimal — status every 10 attempts, errors, and ticket found events
- **ticket_automation.log**: Detailed operation log

Browser library debug output is suppressed for clean console output.

## Troubleshooting

**Chrome debugging connection fails**
- Close all Chrome windows and relaunch with `--remote-debugging-port=9222`
- Check if port 9222 is in use: `lsof -i :9222` (macOS/Linux) or `netstat -ano | findstr 9222` (Windows)

**Session keeps expiring**
- Make sure you're logged into the SRT site in Chrome before starting
- The automation will auto re-login using Chrome's saved credentials

**Browser steals focus**
- Already handled: Chrome launches with `--no-focus-on-navigate` flag

**Emails not arriving**
- Check `.env` file has `NOTIFY_EMAIL`, `SMTP_EMAIL`, `SMTP_PASSWORD` set
- For Gmail, you need an app password: https://myaccount.google.com/apppasswords

**terminal-notifier not found (macOS)**
```bash
brew install terminal-notifier
```

## License

MIT
