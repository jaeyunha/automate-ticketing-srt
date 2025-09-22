# SRT Ticket Automation

An automated ticket booking system for SRT (Super Rapid Train) that continuously searches for available tickets and notifies you when found.

## Features

- **Automated ticket searching** with continuous monitoring
- **Email notifications** when tickets are found
- **macOS notifications** with sound alerts
- **Enhanced error handling** with automatic retry mechanisms
- **Browser restart capability** for CDP connection issues
- **Comprehensive logging** for debugging and monitoring

## Recent Improvements (Error Handling & Auto-Retry)

The automation now includes robust error handling to prevent crashes and automatically recover from common issues:

### 🔄 Automatic Retry Mechanisms
- **CDP Error Recovery**: Automatically retries operations when Chrome DevTools Protocol errors occur
- **Browser Restart**: Restarts the browser when connection issues persist
- **Progressive Backoff**: Uses increasing delays between retry attempts
- **Consecutive Error Tracking**: Restarts browser after too many consecutive errors

### 🛡️ Error Handling Features
- **Safe Page Operations**: All page interactions wrapped in retry logic
- **Multiple Fallback Methods**: Each form field has multiple ways to be filled
- **Graceful Degradation**: Continues operation even when some methods fail
- **Detailed Logging**: Comprehensive logs for debugging issues

### 📊 Monitoring & Logging
- **File Logging**: All operations logged to `ticket_automation.log`
- **Console Output**: Real-time status updates
- **Error Tracking**: Detailed error messages with context
- **Retry Attempts**: Clear indication of retry attempts and success/failure

## Installation

1. Install dependencies:
```bash
pip install browser-use
```

2. Set up environment variables:
```bash
export GOOGLE_API_KEY="your_google_api_key"
```

## Usage

### Basic Usage
```bash
python main.py
```

### Enhanced Usage (Recommended)
```bash
python run_automation.py
```

The enhanced runner provides:
- Better error handling
- Automatic retry on failures
- Detailed logging
- User-friendly status messages

## Configuration

Edit the parameters in `main.py` or `run_automation.py`:

```python
await main(
    date="20251003",           # Date in YYYYMMDD format
    departure_time="200000",   # Time in HHMMSS format (24-hour)
    number_of_ticket="2",      # Number of tickets to book
    max_restarts=5             # Maximum restart attempts
)
```

## Error Recovery

The system automatically handles these common issues:

### CDP Errors
- `No target with given id found`
- `Node does not have a layout object`
- `Node with given id does not belong to the document`

### Browser Issues
- Connection timeouts
- Page load failures
- Element interaction failures

### Recovery Actions
1. **Immediate Retry**: Retry the operation with exponential backoff
2. **Browser Restart**: Restart browser if retries fail
3. **Full Restart**: Restart entire automation if browser restart fails
4. **Notification**: Alert user if all recovery attempts fail

## Logging

Logs are written to:
- `ticket_automation.log` - Detailed operation logs
- `automation_runner.log` - Runner-specific logs
- Console output - Real-time status

## Troubleshooting

### Common Issues

1. **CDP Connection Errors**
   - The system will automatically retry and restart
   - Check Chrome is running with debugging enabled
   - Ensure port 9222 is available

2. **Element Not Found**
   - Multiple fallback methods are used
   - Check if the website structure has changed
   - Review logs for specific error details

3. **Browser Crashes**
   - Automatic browser restart is implemented
   - Check system resources
   - Review Chrome version compatibility

### Manual Recovery

If the automation fails completely:
1. Check the log files for error details
2. Restart Chrome with debugging enabled
3. Run the automation again
4. The system will automatically retry failed operations

## Files

- `main.py` - Core automation logic with enhanced error handling
- `run_automation.py` - Enhanced runner with better user experience
- `notification.py` - macOS notification system
- `send_email.py` - Email notification system
- `ticket_automation.log` - Detailed operation logs
- `automation_runner.log` - Runner logs

## Requirements

- Python 3.7+
- Chrome browser with debugging enabled
- macOS (for notifications)
- Internet connection
- Google API key (for LLM features, if used)
