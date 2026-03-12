#!/usr/bin/env python3
"""
Enhanced Ticket Automation Runner

This script runs the ticket automation with improved error handling and automatic retry.
It will automatically restart the browser and retry operations when CDP errors occur.
"""

import argparse
import asyncio
import logging
from main import main

# Configure logging (force override any existing config from imported libraries)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()
formatter = logging.Formatter('%(asctime)s  %(levelname)-5s  %(message)s', datefmt='%H:%M:%S')
file_handler = logging.FileHandler('ticket_automation.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)

async def run_automation(args):
    """Run the ticket automation with enhanced error handling"""
    try:
        logging.info("Starting enhanced ticket automation...")
        logging.info(f"Route: {args.departure} -> {args.arrival}")
        logging.info(f"Date: {args.date}, Time: {args.time}, Tickets: {args.tickets}" +
                     (f", Max arrival: {args.max_arrival}" if args.max_arrival else ""))

        await main(
            date=args.date,
            departure_time=args.time,
            number_of_ticket=args.tickets,
            departure=args.departure,
            arrival=args.arrival,
            include_first_class=args.first_class,
            max_arrival=args.max_arrival,
            max_restarts=args.max_restarts,
        )

        logging.info("Ticket automation completed successfully!")

    except Exception as e:
        logging.error(f"Automation failed completely: {e}")
        print(f"\n❌ Automation failed: {e}")
        print("Check the logs for more details.")
        return False

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SRT Ticket Automation")
    parser.add_argument("--departure", default="동대구", help="Departure station (default: 동대구)")
    parser.add_argument("--arrival", default="수서", help="Arrival station (default: 수서)")
    parser.add_argument("--date", default="20260314", help="Travel date in YYYYMMDD format (default: 20260314)")
    parser.add_argument("--time", default="080000", help="Departure time in HHMMSS format (default: 080000)")
    parser.add_argument("--tickets", default="2", help="Number of tickets (default: 2)")
    parser.add_argument("--first-class", action="store_true", help="Also check 특실 (first class) seats")
    parser.add_argument("--max-arrival", default=None, help="Max arrival time in HHMM format, e.g. 1200 (default: no limit)")
    parser.add_argument("--max-restarts", type=int, default=5, help="Max browser restarts (default: 5)")
    args = parser.parse_args()

    seat_types = "일반실 + 예약대기"
    if args.first_class:
        seat_types += " + 특실"

    print("🚀 Starting Enhanced Ticket Automation")
    print(f"  Route: {args.departure} → {args.arrival}")
    print(f"  Date: {args.date}, Time: {args.time}, Tickets: {args.tickets}")
    if args.max_arrival:
        print(f"  Max arrival: {args.max_arrival[:2]}:{args.max_arrival[2:]}")
    print(f"  Seat types: {seat_types}")
    print("\nPress Ctrl+C to stop the automation\n")

    try:
        success = asyncio.run(run_automation(args))
        if success:
            print("\n✅ Automation completed successfully!")
        else:
            print("\n❌ Automation failed. Check logs for details.")
    except KeyboardInterrupt:
        print("\n⏹️  Automation stopped by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
