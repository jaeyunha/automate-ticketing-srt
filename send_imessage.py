#!/usr/bin/env python3
"""
iMessage Sender using AppleScript

This script allows you to send iMessage messages using AppleScript on macOS.
It provides both a simple function interface and a command-line interface.
"""

import subprocess
import sys
import argparse
import json
from typing import Optional, List


def send_imessage(phone_number: str, message: str, contact_name: Optional[str] = None) -> bool:
    """
    Send an iMessage using AppleScript.
    
    Args:
        phone_number: The phone number or email address to send to
        message: The message content to send
        contact_name: Optional contact name for display purposes
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    # Escape special characters in the message for AppleScript
    escaped_message = message.replace('"', '\\"').replace('\\', '\\\\')
    
    # Create the AppleScript command
    if contact_name:
        applescript = f'''
        tell application "Messages"
            set targetService to 1st service whose service type = iMessage
            set targetBuddy to buddy "{phone_number}" of targetService
            set targetBuddy's name to "{contact_name}"
            send "{escaped_message}" to targetBuddy
        end tell
        '''
    else:
        applescript = f'''
        tell application "Messages"
            set targetService to 1st service whose service type = iMessage
            set targetBuddy to buddy "{phone_number}" of targetService
            send "{escaped_message}" to targetBuddy
        end tell
        '''
    
    try:
        # Execute the AppleScript
        subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Message sent successfully to {phone_number}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error sending message: {e}")
        print(f"AppleScript error: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def send_imessage_to_multiple(recipients: List[dict], message: str) -> dict:
    """
    Send the same message to multiple recipients.
    
    Args:
        recipients: List of dictionaries with 'phone_number' and optional 'name' keys
        message: The message content to send
        
    Returns:
        dict: Results of sending to each recipient
    """
    results = {}
    
    for recipient in recipients:
        phone_number = recipient['phone_number']
        contact_name = recipient.get('name')
        
        print(f"Sending message to {contact_name or phone_number}...")
        success = send_imessage(phone_number, message, contact_name)
        results[phone_number] = success
        
    return results


def check_messages_app() -> bool:
    """
    Check if Messages app is available and iMessage is configured.
    
    Returns:
        bool: True if Messages app is available, False otherwise
    """
    try:
        applescript = '''
        tell application "System Events"
            if (name of processes) contains "Messages" then
                return "running"
            else
                return "not running"
            end if
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            check=True
        )
        
        return "running" in result.stdout
        
    except Exception:
        return False


def main():
    """Command-line interface for the iMessage sender."""
    parser = argparse.ArgumentParser(
        description="Send iMessage using AppleScript",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send a simple message
  python send-imessage.py "+1234567890" "Hello, this is a test message!"
  
  # Send with contact name
  python send-imessage.py "+1234567890" "Hello!" --name "John Doe"
  
  # Send to multiple recipients from JSON file
  python send-imessage.py --recipients recipients.json "Hello everyone!"
  
  # Send to email address
  python send-imessage.py "john@example.com" "Hello via email!"
        """
    )
    
    parser.add_argument(
        'phone_number',
        nargs='?',
        help='Phone number or email address to send to'
    )
    parser.add_argument(
        'message',
        nargs='?',
        help='Message content to send'
    )
    parser.add_argument(
        '--name', '-n',
        help='Contact name for display purposes'
    )
    parser.add_argument(
        '--recipients', '-r',
        help='JSON file containing list of recipients with phone_number and optional name'
    )
    parser.add_argument(
        '--check-app',
        action='store_true',
        help='Check if Messages app is available'
    )
    
    args = parser.parse_args()
    
    # Check if Messages app is available
    if args.check_app:
        if check_messages_app():
            print("✓ Messages app is available")
        else:
            print("✗ Messages app is not available or not running")
            print("Please make sure Messages app is installed and iMessage is configured.")
        return
    
    # Handle multiple recipients from JSON file
    if args.recipients:
        if not args.message:
            print("Error: Message is required when using --recipients")
            sys.exit(1)
            
        try:
            with open(args.recipients, 'r') as f:
                recipients = json.load(f)
            
            if not isinstance(recipients, list):
                print("Error: Recipients file must contain a JSON array")
                sys.exit(1)
            
            results = send_imessage_to_multiple(recipients, args.message)
            
            # Print summary
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            print(f"\nSummary: {successful}/{total} messages sent successfully")
            
        except FileNotFoundError:
            print(f"Error: Recipients file '{args.recipients}' not found")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in recipients file '{args.recipients}'")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    # Handle single recipient
    elif args.phone_number and args.message:
        success = send_imessage(args.phone_number, args.message, args.name)
        if not success:
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
