import subprocess
import sys

def send_email_with_mutt(recipient, subject, body):
    """
    Sends an email using the 'mutt' command-line client.

    This function constructs and executes a shell command to send an email.
    It requires 'mutt' to be installed and configured on the system.

    Args:
        recipient (str): The email address of the recipient.
        subject (str): The subject of the email.
        body (str): The body content of the email.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    try:
        # We use a shell pipeline to pass the body to mutt's standard input.
        # The `echo` command prints the body, and the `|` (pipe) sends that
        # output to the `mutt` command.
        # NOTE: Using shell=True can be a security risk if you don't control
        # the input. Here we assume the recipient, subject, and body are trusted.
        command = f'echo "{body}" | mutt -s "{subject}" -- "{recipient}"'

        print(f"Executing command: {command}")

        # subprocess.run executes the command.
        # - check=True: Raises an exception if the command returns a non-zero exit code (i.e., fails).
        # - shell=True: Needed to interpret the pipe '|' character.
        # - capture_output=True: Captures stdout and stderr.
        # - text=True: Decodes stdout and stderr as text.
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )

        print("Email sent successfully!")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        return True
    except FileNotFoundError:
        # This error occurs if the 'mutt' command itself isn't found.
        print(
            "Error: 'mutt' command not found. Is mutt installed and in your system's PATH?",
            file=sys.stderr
        )
        return False
    except subprocess.CalledProcessError as e:
        # This error occurs if mutt runs but exits with an error code.
        print(
            f"Error executing mutt. It's likely a configuration issue. Return code: {e.returncode}",
            file=sys.stderr
        )
        print(f"STDERR:\n{e.stderr}", file=sys.stderr)
        return False
    except Exception as e:
        # Catch any other unexpected errors.
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return False

# This block runs only when the script is executed directly (e.g., `python send_email.py`)
if __name__ == "__main__":
    # --- CONFIGURE YOUR TEST EMAIL HERE ---
    # IMPORTANT: Change this to a real email address to test.
    test_recipient = "jaeyunha0317@gmail.com"
    test_subject = "Notification to get tickets"
    test_body = (
        "Hello from Arch Linux!\n\n"
        "This email was composed and sent automatically by a Python script.\n"
        "It uses the 'subprocess' module to launch the 'mutt' mail client."
    )

    print("--- Attempting to send a test email ---")
    if send_email_with_mutt(test_recipient, test_subject, test_body):
        print("\nTest finished successfully.")
    else:
        print("\nTest failed. Please check the error messages above.")
        print("Ensure 'mutt' is installed and your ~/.muttrc is configured correctly.")
