# SRT Ticket Automation

An automated ticket booking system for SRT (Super Rapid Train) that continuously searches for available tickets and notifies you when found.

## 🚀 Features

- **Automated ticket searching** with continuous monitoring
- **Email notifications** when tickets are found (via AppleScript)
- **macOS notifications** with sound alerts
- **iMessage notifications** (optional)
- **Robust error handling** with automatic retry mechanisms
- **Browser restart capability** for connection issues
- **Comprehensive logging** for debugging

## 📋 Requirements

- **Python 3.12+**
- **macOS** (for notifications and AppleScript)
- **Chrome browser** with debugging enabled
- **Mail app** configured (for email notifications)
- **Messages app** (for iMessage notifications, optional)

## 🛠️ Installation

1. **Install dependencies:**
```bash
pip install browser-use desktop-notifier macos-notifications
```

2. **Set up Chrome debugging:**
```bash
# Start Chrome with debugging enabled
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

3. **Install terminal-notifier (for macOS notifications):**
```bash
brew install terminal-notifier
```

## 🎯 Usage

### Quick Start
```bash
python run_automation.py
```

### Basic Usage
```bash
python main.py
```

### Configuration
Edit the parameters in `run_automation.py`:

```python
await main(
    date="20251003",           # Date in YYYYMMDD format
    departure_time="200000",   # Time in HHMMSS format (24-hour)
    number_of_ticket="2",      # Number of tickets to book
    max_restarts=5             # Maximum restart attempts
)
```

## 📁 Project Structure

```
automate-ticketing/
├── main.py                 # Core automation logic
├── run_automation.py       # Enhanced runner with better UX
├── notification.py         # macOS notification system
├── send_email.py          # Email notifications via AppleScript
├── send_imessage.py       # iMessage notifications (optional)
├── example_usage.py       # Usage examples
├── email_recipients.json  # Email recipient configuration
└── pyproject.toml         # Project dependencies
```

## 🔧 How It Works

1. **Browser Automation**: Uses `browser-use` to control Chrome
2. **Form Filling**: Automatically fills departure/destination, date, time, and ticket count
3. **Continuous Search**: Repeatedly searches for available tickets
4. **Ticket Detection**: Uses XPath to find "예약하기" (Reserve) buttons
5. **Notifications**: Sends email and macOS notifications when tickets are found
6. **Error Recovery**: Automatically retries on failures with exponential backoff

## 📧 Notification System

### Email Notifications
- Uses AppleScript to send emails via Mail app
- Configure recipients in `email_recipients.json`
- Supports multiple recipients

### macOS Notifications
- Uses `terminal-notifier` for system notifications
- Includes sound alerts
- Shows ticket availability status

### iMessage Notifications (Optional)
- Uses AppleScript to send iMessages
- Supports phone numbers and email addresses
- Requires Messages app to be configured

## 🛡️ Error Handling

The system includes robust error handling:

- **CDP Error Recovery**: Automatically retries Chrome DevTools Protocol errors
- **Browser Restart**: Restarts browser when connection issues persist
- **Progressive Backoff**: Uses increasing delays between retry attempts
- **Multiple Fallback Methods**: Each form field has multiple ways to be filled
- **Comprehensive Logging**: All operations logged to `ticket_automation.log`

## 📊 Logging

Logs are written to:
- `ticket_automation.log` - Detailed operation logs
- `automation_runner.log` - Runner-specific logs
- Console output - Real-time status updates

## 🚨 Troubleshooting

### Common Issues

1. **Chrome Debugging Not Enabled**
   ```bash
   # Start Chrome with debugging
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
   ```

2. **Mail App Not Configured**
   - Open Mail app and set up your email account
   - Test email sending manually

3. **Terminal Notifier Not Found**
   ```bash
   brew install terminal-notifier
   ```

4. **Browser Connection Issues**
   - The system will automatically retry and restart
   - Check Chrome is running with debugging enabled
   - Ensure port 9222 is available

## 📝 Example Usage

```python
# Test email notifications
python send_email.py "recipient@example.com" "Test Subject" "Hello!"

# Test macOS notifications
python notification.py

# Test iMessage (requires Messages app)
python send_imessage.py "+1234567890" "Hello from Python!"
```

## 🔄 Automation Flow

1. **Start**: Launch Chrome with debugging enabled
2. **Navigate**: Go to SRT booking website
3. **Fill Form**: Enter departure (수서), destination (동대구), date, time, ticket count
4. **Search**: Click search button
5. **Check**: Look for "예약하기" buttons in results
6. **Notify**: Send email and macOS notifications if tickets found
7. **Repeat**: Continue searching until tickets are found or stopped

## 📄 License

MIT License - see LICENSE file for details.
