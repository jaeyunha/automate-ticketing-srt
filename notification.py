import subprocess
import sys
import time

def send_notification(title, message, sound="default", subtitle="", action_button="", url=""):
    """Send a macOS notification using terminal-notifier"""
    try:
        # Use terminal-notifier to send notification
        time.sleep(3)
        cmd = [
            'terminal-notifier',
            '-title', title,
            '-message', message,
            '-sound', sound
        ]
        
        # Add optional parameters
        if subtitle:
            cmd.extend(['-subtitle', subtitle])
        if action_button:
            cmd.extend(['-actions', action_button])
        if url:
            cmd.extend(['-open', url])
            
        subprocess.run(cmd, check=True)
        print(f"Notification sent: {title} - {message}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to send notification: {e}")
    except Exception as e:
        print(f"Error sending notification: {e}")

if __name__ == "__main__":
    send_notification(
        title="Ticket Found!",
        message="Buy within 10 minutes",
        subtitle="Korail SRT Booking",
        sound="Frog",
        url="https://etk.srail.kr"
    )