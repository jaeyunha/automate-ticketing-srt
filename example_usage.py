#!/usr/bin/env python3
"""
Example usage of the iMessage sender script.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from send_imessage import send_imessage, send_imessage_to_multiple, check_messages_app
from send_email import send_email, send_email_to_multiple, check_mail_app


def main():
    # print("iMessage Sender Example")
    # print("=" * 30)
    
    # # Check if Messages app is available
    # if not check_messages_app():
    #     print("Messages app is not available. Please make sure it's installed and running.")
    #     return
    
    # # Example 1: Send a simple message
    # print("\n1. Sending a simple message...")
    # success = send_imessage(
    #     phone_number="jaeyunha0317@gmail.com",  # Replace with actual email
    #     message="@Jaeyun hello this is test message, please reply back as soon as possible"
    # )
    
    # if success:
    #     print("✓ Message sent successfully!")
    # else:
    #     print("✗ Failed to send message")
    
    # # Example 2: Send message with contact name
    # print("\n2. Sending message with contact name...")
    # success = send_imessage(
    #     phone_number="+19253916231",  # Replace with actual phone number
    #     message="Hello John! This message has a contact name.",
    #     contact_name="Jaeyun Ha"
    # )
    
    # # Example 3: Send to multiple recipients
    # print("\n3. Sending to multiple recipients...")
    # recipients = [
    #     {"phone_number": "+19253916231", "name": "Jaeyun Ha"},
    #     {"phone_number": "jaeyunha0317@gmail.com"}  # Can also use email
    # ]
    
    # results = send_imessage_to_multiple(
    #     recipients=recipients,
    #     message="Hello everyone! This is a group message from Python."
    # )
    
    # # Print results
    # for phone_number, success in results.items():
    #     status = "✓" if success else "✗"
    #     print(f"{status} {phone_number}")

    # Email testing
    print("\n4. Sending an email...")
    email_success = send_email(
        to_email="jaeyunha0317@gmail.com",
        subject="Test Subject for notification test",
        message="Hello from Python and notification test",
    )
    
    if email_success:
        print("✓ Email sent successfully!")
    else:
        print("✗ Failed to send email")
    
    

if __name__ == "__main__":
    main()
