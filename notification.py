"""
Cross-platform desktop notification.

- macOS: uses terminal-notifier (brew install terminal-notifier)
- Linux/Windows: uses desktop-notifier (pip package, already in dependencies)
"""

import subprocess
import platform
import logging


def send_notification(title, message, sound="default", subtitle="", action_button="", url=""):
    """Send a desktop notification. Works on macOS, Linux, and Windows."""
    system = platform.system()

    if system == "Darwin":
        _send_macos(title, message, sound, subtitle, action_button, url)
    else:
        _send_cross_platform(title, message)


def _send_macos(title, message, sound, subtitle, action_button, url):
    """macOS notification via terminal-notifier."""
    try:
        cmd = ['terminal-notifier', '-title', title, '-message', message, '-sound', sound]
        if subtitle:
            cmd.extend(['-subtitle', subtitle])
        if action_button:
            cmd.extend(['-actions', action_button])
        if url:
            cmd.extend(['-open', url])
        subprocess.run(cmd, check=True, capture_output=True)
        logging.info(f"Desktop notification sent: {title}")
    except FileNotFoundError:
        logging.warning("terminal-notifier not found, falling back to cross-platform")
        _send_cross_platform(title, message)
    except Exception as e:
        logging.error(f"macOS notification failed: {e}")


def _send_cross_platform(title, message):
    """Cross-platform notification via desktop-notifier."""
    try:
        from desktop_notifier import DesktopNotifier
        import asyncio

        async def _notify():
            notifier = DesktopNotifier()
            await notifier.send(title=title, message=message)

        asyncio.get_event_loop().run_until_complete(_notify())
        logging.info(f"Desktop notification sent: {title}")
    except ImportError:
        logging.warning("desktop-notifier not installed — skipping desktop notification")
    except Exception as e:
        logging.error(f"Desktop notification failed: {e}")


if __name__ == "__main__":
    send_notification(
        title="Ticket Found!",
        message="Buy within 10 minutes",
        subtitle="SRT Booking",
        sound="Frog",
        url="https://etk.srail.kr"
    )
