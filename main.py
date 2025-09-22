import asyncio
import sys
from browser_use import Browser
import os 
import logging
import platform
from notification import send_notification
from send_email import send_email
from send_email_linux import send_email_with_mutt

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ticket_automation.log'),
        logging.StreamHandler()
    ]
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class TicketAutomationError(Exception):
    """Custom exception for ticket automation errors"""
    pass


async def create_browser():
    """Create and start a browser instance with error handling"""
    if platform.system() == "Darwin":
        executable_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        user_data_dir = '~/Library/Application Support/Google/Chrome'
    else:
        executable_path = '/opt/google/chrome/google-chrome'
        user_data_dir = '~/.config/google-chrome'
    try:
        browser = Browser(
            record_video_dir="./recordings",
            cdp_url="http://localhost:9222",
            executable_path=executable_path,
            user_data_dir=user_data_dir,
            headless=False,
        )
        await browser.start()
        return browser
    except Exception as e:
        logging.error(f"Failed to create browser: {e}")
        raise TicketAutomationError(f"Browser creation failed: {e}")

async def safe_page_operation(operation, max_retries=3, delay=2):
    """Safely execute page operations with retry logic"""
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['cdp', 'target', 'layout', 'document']):
                logging.warning(f"CDP error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay * (attempt + 1))  # Exponential backoff
                    continue
            raise e
    raise TicketAutomationError(f"Operation failed after {max_retries} attempts")

async def main(date, departure_time, number_of_ticket, max_restarts=5):
    """Main function with automatic restart capability"""
    restart_count = 0
    
    while restart_count < max_restarts:
        try:
            logging.info(f"Starting ticket automation (attempt {restart_count + 1}/{max_restarts})")
            await run_ticket_search(date, departure_time, number_of_ticket)
            break  # Success, exit the retry loop
            
        except TicketAutomationError as e:
            restart_count += 1
            logging.error(f"Ticket automation failed (attempt {restart_count}): {e}")
            
            if restart_count < max_restarts:
                wait_time = min(30, 5 * restart_count)  # Progressive backoff, max 30 seconds
                logging.info(f"Restarting in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logging.error("Maximum restart attempts reached. Exiting.")
                send_notification(
                    title="Ticket Automation Failed",
                    message=f"Failed after {max_restarts} attempts. Check logs.",
                    sound="Basso"
                )
                raise
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            restart_count += 1
            if restart_count < max_restarts:
                await asyncio.sleep(10)
            else:
                raise

async def run_ticket_search(date, departure_time, number_of_ticket):
    """Core ticket search logic with error handling"""
    browser = None
    try:
        browser = await create_browser()

        # 1. Actor: Precise navigation and element interactions
        page = await safe_page_operation(
            lambda: browser.new_page("https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000")
        )
        
        # Wait a moment for the page to load
        await asyncio.sleep(3)
        
        # Fill departure and destination cities with error handling
        await safe_page_operation(lambda: fill_cities(page))
        
        # Fill form fields with error handling
        await safe_page_operation(lambda: fill_form_fields(page, date, departure_time, number_of_ticket))
        
        # Start the continuous ticket checking loop
        await continuous_ticket_search(page, date, departure_time)
        
    except Exception as e:
        logging.error(f"Error in ticket search: {e}")
        raise TicketAutomationError(f"Ticket search failed: {e}")
    finally:
        if browser:
            try:
                await browser.stop()
            except Exception as e:
                logging.warning(f"Error stopping browser: {e}")

async def fill_cities(page):
    """Fill departure and destination cities"""
    departure_city = await page.get_elements_by_css_selector("#dptRsStnCdNm")
    destination_city = await page.get_elements_by_css_selector("#arvRsStnCdNm")
    
    # Check if elements were found
    if departure_city and destination_city:
        await departure_city[0].fill("수서", clear_existing=True)
        await destination_city[0].fill("동대구", clear_existing=True)
        logging.info("Successfully filled departure and destination cities")
    else:
        logging.warning("Could not find departure or destination city elements")
        raise TicketAutomationError("City elements not found")

async def fill_form_fields(page, date, departure_time, number_of_ticket):
    """Fill all form fields with error handling"""
    # Handle date dropdown
    await safe_page_operation(lambda: fill_date_field(page, date))
    
    # Handle departure time dropdown
    await safe_page_operation(lambda: fill_time_field(page, departure_time))
    
    # Handle number of tickets dropdown
    await safe_page_operation(lambda: fill_ticket_count_field(page, number_of_ticket))

async def fill_date_field(page, date):
    """Fill date field with multiple fallback methods"""
    try:
        # Method 1: Use JavaScript to directly set the value (most reliable)
        await page.evaluate("() => { document.getElementById('dptDt').value = '" + date + "'; }")
        logging.info("Successfully selected date using JavaScript")
        
        # Method 2: Alternative - remove selected from all options, then add to target option
        await page.evaluate(f"""
            () => {{
                const select = document.getElementById('dptDt');
                const options = select.querySelectorAll('option');
                options.forEach(option => option.removeAttribute('selected'));
                const targetOption = select.querySelector('option[value="{date}"]');
                if (targetOption) {{
                    targetOption.setAttribute('selected', 'selected');
                    select.value = '{date}';
                }}
            }}
        """)
        logging.info("Successfully selected date by modifying HTML attributes")
        
    except Exception as e:
        logging.warning(f"Direct HTML modification failed: {e}")
        # Fallback to the original select_option method
        try:
            date_element = await page.get_elements_by_css_selector("#dptDt")
            if date_element:
                await date_element[0].select_option(date)
                logging.info("Successfully selected date using select_option fallback")
        except Exception as e2:
            logging.error(f"All date selection methods failed: {e2}")
            raise TicketAutomationError("Date selection failed")

async def fill_time_field(page, departure_time):
    """Fill departure time field with multiple fallback methods"""
    try:
        # Method 1: Use JavaScript to directly set the value (most reliable)
        await page.evaluate(f"() => {{ document.getElementById('dptTm').value = '{departure_time}'; }}")
        logging.info("Successfully selected departure time using JavaScript")
        
        # Method 2: Alternative - remove selected from all options, then add to target option
        await page.evaluate(f"""
            () => {{
                const select = document.getElementById('dptTm');
                const options = select.querySelectorAll('option');
                options.forEach(option => option.removeAttribute('selected'));
                const targetOption = select.querySelector('option[value="{departure_time}"]');
                if (targetOption) {{
                    targetOption.setAttribute('selected', 'selected');
                    select.value = '{departure_time}';
                }}
            }}
        """)
        logging.info("Successfully selected departure time by modifying HTML attributes")
        
    except Exception as e:
        logging.warning(f"Direct HTML modification for departure_time failed: {e}")
        # Fallback to the original select_option method
        try:
            departure_time_element = await page.get_elements_by_css_selector("#dptTm")
            if departure_time_element:
                await departure_time_element[0].select_option(departure_time)
                logging.info("Successfully selected departure time using select_option fallback")
        except Exception as e2:
            logging.error(f"All departure_time selection methods failed: {e2}")
            raise TicketAutomationError("Time selection failed")

async def fill_ticket_count_field(page, number_of_ticket):
    """Fill ticket count field with multiple fallback methods"""
    try:
        # Method 1: Use JavaScript to directly set the value (most reliable)
        await page.evaluate(f"() => {{ document.getElementById('psgInfoPerPrnb1').value = '{number_of_ticket}'; }}")
        logging.info("Successfully selected number of tickets using JavaScript")
        
        # Method 2: Alternative - remove selected from all options, then add to target option
        await page.evaluate(f"""
            () => {{
                const select = document.getElementById('psgInfoPerPrnb1');
                const options = select.querySelectorAll('option');
                options.forEach(option => option.removeAttribute('selected'));
                const targetOption = select.querySelector('option[value="{number_of_ticket}"]');
                if (targetOption) {{
                    targetOption.setAttribute('selected', 'selected');
                    select.value = '{number_of_ticket}';
                }}
            }}
        """)
        logging.info("Successfully selected number of tickets by modifying HTML attributes")
        
    except Exception as e:
        logging.warning(f"Direct HTML modification for ticket count failed: {e}")
        # Fallback to the original select_option method
        try:
            number_of_ticket_selected = await page.get_elements_by_css_selector("#psgInfoPerPrnb1")
            if number_of_ticket_selected:
                await number_of_ticket_selected[0].select_option(number_of_ticket)
                logging.info("Successfully selected number of tickets using select_option fallback")
        except Exception as e2:
            logging.error(f"All ticket count selection methods failed: {e2}")
            raise TicketAutomationError("Ticket count selection failed")

async def continuous_ticket_search(page, date, departure_time):
    """Continuous ticket checking loop with error handling"""
    attempt = 1
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    while True:
        try:
            logging.info(f"=== Ticket Search Attempt #{attempt} ===")
            
            # Handle search button with error handling
            await safe_page_operation(lambda: click_search_button(page))
            
            # Wait for search results to load
            await asyncio.sleep(3)
            
            # Check for available tickets
            tickets_found = await safe_page_operation(lambda: check_for_tickets(page))
            
            if tickets_found:
                logging.info("🎉 TICKET FOUND! Exiting search loop")
                break
            
            # Re-fill the form after refresh
            await safe_page_operation(lambda: refill_form_after_search(page, date, departure_time))
            
            attempt += 1
            consecutive_errors = 0  # Reset error counter on successful iteration
            
        except Exception as e:
            consecutive_errors += 1
            logging.error(f"Error in ticket search attempt {attempt}: {e}")
            
            if consecutive_errors >= max_consecutive_errors:
                logging.error(f"Too many consecutive errors ({consecutive_errors}). Restarting browser.")
                raise TicketAutomationError(f"Too many consecutive errors: {consecutive_errors}")
            
            # Wait before retrying
            await asyncio.sleep(5)
            attempt += 1

async def click_search_button(page):
    """Click the search button with error handling"""
    search_button = await page.get_elements_by_css_selector("input[type='submit']")
    if search_button:
        await search_button[0].click()
        logging.info("Successfully clicked search button")
    else:
        logging.error("Could not find search button")
        raise TicketAutomationError("Search button not found")

async def check_for_tickets(page):
    """Check for available tickets and handle ticket booking"""
    try:
        # Method 1: Use XPath to find all reservation links in the 7th column
        reservation_found = await page.evaluate("""
            () => {
                // Find all reservation links in the 7th column of any row
                const xpath = "//*[@id='result-form']//tbody//tr//td[7]/a";
                const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                
                const availableLinks = [];
                // Check if any links contain "예약하기" text
                for (let i = 0; i < result.snapshotLength; i++) {
                    const link = result.snapshotItem(i);
                    if (link && link.textContent && link.textContent.includes('예약하기')) {
                        availableLinks.push({
                            text: link.textContent,
                            href: link.href
                        });
                    }
                }
                return availableLinks;
            }
        """)
        
        # Parse the result properly
        import json
        try:
            if isinstance(reservation_found, str):
                reservation_found = json.loads(reservation_found)
            logging.info(f"Found {len(reservation_found)} available tickets")
            
            if len(reservation_found) > 0:
                logging.info("Available tickets:")
                for i, ticket in enumerate(reservation_found):
                    logging.info(f"  Ticket {i+1}: {ticket['text']}")
                
                # Click the first available ticket
                click_result = await page.evaluate("""
                    () => {
                        const xpath = "//*[@id='result-form']//tbody//tr//td[7]/a";
                        const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                        
                        const availableLinks = [];
                        for (let i = 0; i < result.snapshotLength; i++) {
                            const link = result.snapshotItem(i);
                            if (link && link.textContent && link.textContent.includes('예약하기')) {
                                availableLinks.push(link);
                            }
                        }
                        
                        if (availableLinks.length > 0) {
                            // Select the first available ticket
                            availableLinks[0].click();
                            return true;
                        }
                        return false;
                    }
                """)
                
                if click_result:
                    logging.info("🎉 TICKET FOUND! Successfully clicked reservation button")
                    await handle_ticket_found()
                    return True
                else:
                    logging.warning("Failed to click reservation button")
            else:
                logging.info("No tickets available yet")
        except Exception as parse_error:
            logging.error(f"Error parsing reservation results: {parse_error}")
            logging.info("No tickets available yet")
            
    except Exception as e:
        logging.error(f"XPath method failed: {e}")
        logging.info("No tickets available yet (XPath method failed)")
    
    return False

async def handle_ticket_found():
    """Handle notification when ticket is found"""
    email_contents = {
        "subject": "Ticket Found (SRT) - Buy within 10 minutes",
        "message": "Hello from ticketing automation, buy within 10 minutes",
        "recipient": "jaeyunha0317@gmail.com",
    }
    if platform.system() == "Darwin":

        email_success = send_email(
            to_email=email_contents["recipient"],
            subject=email_contents["subject"],
            message=email_contents["message"],
        )
    else:
        email_success = send_email_with_mutt(
            recipient=email_contents["recipient"],
            subject=email_contents["subject"],
            body=email_contents["message"],
        )
    
    if email_success:
        logging.info("✓ Email sent successfully!")
    else:
        logging.error("✗ Failed to send email")
    
    send_notification(
        title="Ticket Found!",
        message="Buy within 10 minutes",
        sound="Frog"
    )

async def refill_form_after_search(page, date, departure_time):
    """Re-fill the form after search results"""
    # Re-fill departure and destination cities
    departure_city = await page.get_elements_by_css_selector("#dptRsStnCdNm")
    destination_city = await page.get_elements_by_css_selector("#arvRsStnCdNm")
    
    if departure_city and destination_city:
        await departure_city[0].fill("수서", clear_existing=True)
        await destination_city[0].fill("동대구", clear_existing=True)
        logging.info("Re-filled departure and destination cities")

    # Re-select date and departure_time after refresh
    try:
        # Wait a bit more for the page to fully load
        await asyncio.sleep(3)
        
        # Check if elements exist before trying to set values
        date_element_exists = await page.evaluate("() => document.getElementById('dptDt') !== null")
        departure_time_element_exists = await page.evaluate("() => document.getElementById('dptTm') !== null")
        
        if date_element_exists:
            await page.evaluate(f"() => {{ document.getElementById('dptDt').value = '{date}'; }}")
            logging.info("Re-selected date")
        else:
            logging.warning("Date element not found after refresh")
            
        if departure_time_element_exists:
            await page.evaluate(f"() => {{ document.getElementById('dptTm').value = '{departure_time}'; }}")
            logging.info("Re-selected departure_time")
        else:
            logging.warning("Time element not found after refresh")
            
    except Exception as e:
        logging.error(f"Failed to re-select date/departure_time: {e}")
        raise TicketAutomationError("Form refill failed")

if __name__ == "__main__":
    asyncio.run(main(date="20251003", departure_time="200000", number_of_ticket="2"))
    # asyncio.run(handle_ticket_found())