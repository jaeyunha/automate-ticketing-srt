#!/usr/bin/env python3
"""
Email Sender using AppleScript

This script allows you to send emails using AppleScript on macOS.
It provides both a simple function interface and a command-line interface.
"""

import subprocess
import sys
import argparse
import json
from typing import Optional, List


def send_email(to_email: str, subject: str, message: str, from_email: Optional[str] = None) -> bool:
    """
    Send an email using AppleScript.
    
    Args:
        to_email: The recipient's email address
        subject: The email subject
        message: The email body content
        from_email: Optional sender email address (uses default if not provided)
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Escape special characters in the message and subject for AppleScript
    escaped_subject = subject.replace('"', '\\"').replace('\\', '\\\\')
    escaped_message = message.replace('"', '\\"').replace('\\', '\\\\')
    
    # Create the AppleScript command
    if from_email:
        applescript = f'''
        tell application "Mail"
            set newMessage to make new outgoing message with properties {{subject:"{escaped_subject}", content:"{escaped_message}"}}
            tell newMessage
                set sender to "{from_email}"
                make new to recipient at end of to recipients with properties {{address:"{to_email}"}}
            end tell
            send newMessage
        end tell
        '''
    else:
        applescript = f'''
        tell application "Mail"
            set newMessage to make new outgoing message with properties {{subject:"{escaped_subject}", content:"{escaped_message}"}}
            tell newMessage
                make new to recipient at end of to recipients with properties {{address:"{to_email}"}}
            end tell
            send newMessage
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
        print(f"Email sent successfully to {to_email}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error sending email: {e}")
        print(f"AppleScript error: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def send_email_to_multiple(recipients: List[dict], subject: str, message: str, from_email: Optional[str] = None) -> dict:
    """
    Send the same email to multiple recipients.
    
    Args:
        recipients: List of dictionaries with 'email' and optional 'name' keys
        subject: The email subject
        message: The email body content
        from_email: Optional sender email address
        
    Returns:
        dict: Results of sending to each recipient
    """
    results = {}
    
    for recipient in recipients:
        email = recipient['email']
        name = recipient.get('name', email)
        
        print(f"Sending email to {name}...")
        success = send_email(email, subject, message, from_email)
        results[email] = success
        
    return results


def check_mail_app() -> bool:
    """
    Check if Mail app is available.
    
    Returns:
        bool: True if Mail app is available, False otherwise
    """
    try:
        applescript = '''
        tell application "System Events"
            if (name of processes) contains "Mail" then
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
    """Command-line interface for the email sender."""
    parser = argparse.ArgumentParser(
        description="Send email using AppleScript",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send a simple email
  python send_email.py "recipient@example.com" "Test Subject" "Hello, this is a test email!"
  
  # Send with custom sender
  python send_email.py "recipient@example.com" "Test Subject" "Hello!" --from "sender@example.com"
  
  # Send to multiple recipients from JSON file
  python send_email.py --recipients recipients.json "Test Subject" "Hello everyone!"
  
  # Check if Mail app is available
  python send_email.py --check-app
        """
    )
    
    parser.add_argument(
        'to_email',
        nargs='?',
        help='Recipient email address'
    )
    parser.add_argument(
        'subject',
        nargs='?',
        help='Email subject'
    )
    parser.add_argument(
        'message',
        nargs='?',
        help='Email body content'
    )
    parser.add_argument(
        '--from', '-f',
        dest='from_email',
        help='Sender email address'
    )
    parser.add_argument(
        '--recipients', '-r',
        help='JSON file containing list of recipients with email and optional name'
    )
    parser.add_argument(
        '--check-app',
        action='store_true',
        help='Check if Mail app is available'
    )
    
    args = parser.parse_args()
    
    # Check if Mail app is available
    if args.check_app:
        if check_mail_app():
            print("✓ Mail app is available")
        else:
            print("✗ Mail app is not available or not running")
            print("Please make sure Mail app is installed and configured.")
        return
    
    # Handle multiple recipients from JSON file
    if args.recipients:
        if not args.subject or not args.message:
            print("Error: Subject and message are required when using --recipients")
            sys.exit(1)
            
        try:
            with open(args.recipients, 'r') as f:
                recipients = json.load(f)
            
            if not isinstance(recipients, list):
                print("Error: Recipients file must contain a JSON array")
                sys.exit(1)
            
            results = send_email_to_multiple(recipients, args.subject, args.message, args.from_email)
            
            # Print summary
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            print(f"\nSummary: {successful}/{total} emails sent successfully")
            
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
    elif args.to_email and args.subject and args.message:
        success = send_email(args.to_email, args.subject, args.message, args.from_email)
        if not success:
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
