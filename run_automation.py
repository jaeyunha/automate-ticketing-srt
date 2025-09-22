#!/usr/bin/env python3
"""
Enhanced Ticket Automation Runner

This script runs the ticket automation with improved error handling and automatic retry.
It will automatically restart the browser and retry operations when CDP errors occur.
"""

import asyncio
import logging
from main import main

# Configure logging for the runner
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation_runner.log'),
        logging.StreamHandler()
    ]
)

async def run_automation():
    """Run the ticket automation with enhanced error handling"""
    try:
        logging.info("Starting enhanced ticket automation...")
        
        # Run the main automation with automatic retry
        await main(
            date="20251003",
            departure_time="200000", 
            number_of_ticket="2",
            max_restarts=5  # Automatically restart up to 5 times
        )
        
        logging.info("Ticket automation completed successfully!")
        
    except Exception as e:
        logging.error(f"Automation failed completely: {e}")
        print(f"\n❌ Automation failed: {e}")
        print("Check the logs for more details.")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Enhanced Ticket Automation")
    print("This version includes:")
    print("  ✓ Automatic retry on CDP errors")
    print("  ✓ Browser restart capability")
    print("  ✓ Comprehensive error handling")
    print("  ✓ Detailed logging")
    print("  ✓ Progressive backoff delays")
    print("\nPress Ctrl+C to stop the automation\n")
    
    try:
        success = asyncio.run(run_automation())
        if success:
            print("\n✅ Automation completed successfully!")
        else:
            print("\n❌ Automation failed. Check logs for details.")
    except KeyboardInterrupt:
        print("\n⏹️  Automation stopped by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
