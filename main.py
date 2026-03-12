import asyncio
import subprocess
import sys
from dotenv import load_dotenv
load_dotenv()
from browser_use import Browser
import os
import logging
import platform
from notification import send_notification
from send_email_smtp import send_email_smtp

# Set up logging (only applies if main.py is run directly, otherwise run_automation.py configures it)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-5s  %(message)s',
    datefmt='%H:%M:%S',
)

# Suppress noisy browser_use debug logs
for noisy_logger in ['browser_use', 'cdp_use', 'bubus', 'video_recorder', 'BrowserSession']:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

# Patch out raw print("DEBUG: Evaluating JavaScript: ...") in browser_use
import builtins
_original_print = builtins.print
def _quiet_print(*args, **kwargs):
    if args and isinstance(args[0], str) and args[0].startswith('DEBUG: Evaluating'):
        return
    _original_print(*args, **kwargs)
builtins.print = _quiet_print

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
            highlight_elements=False,
            args=[
                "--no-focus-on-navigate",
                "--disable-background-timer-throttling",
            ],
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

async def main(date, departure_time, number_of_ticket, departure="동대구", arrival="수서", include_first_class=False, max_arrival=None, max_restarts=5):
    """Main function with automatic restart capability"""
    restart_count = 0

    while restart_count < max_restarts:
        try:
            logging.info(f"Starting ticket automation (attempt {restart_count + 1}/{max_restarts})")
            await run_ticket_search(date, departure_time, number_of_ticket, departure, arrival, include_first_class, max_arrival)
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

async def run_ticket_search(date, departure_time, number_of_ticket, departure, arrival, include_first_class, max_arrival=None):
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
        await safe_page_operation(lambda: fill_cities(page, departure, arrival))

        # Fill form fields with error handling
        await safe_page_operation(lambda: fill_form_fields(page, date, departure_time, number_of_ticket))

        # Start the continuous ticket checking loop
        await continuous_ticket_search(page, date, departure_time, number_of_ticket, departure, arrival, include_first_class, max_arrival)
        
    except Exception as e:
        logging.error(f"Error in ticket search: {e}")
        raise TicketAutomationError(f"Ticket search failed: {e}")
    finally:
        if browser:
            try:
                await browser.stop()
            except Exception as e:
                logging.warning(f"Error stopping browser: {e}")

async def fill_cities(page, departure, arrival):
    """Fill departure and destination cities"""
    departure_city = await page.get_elements_by_css_selector("#dptRsStnCdNm")
    destination_city = await page.get_elements_by_css_selector("#arvRsStnCdNm")

    # Check if elements were found
    if departure_city and destination_city:
        await departure_city[0].fill(departure, clear_existing=True)
        await destination_city[0].fill(arrival, clear_existing=True)
    else:
        raise TicketAutomationError("City elements not found")

async def fill_form_fields(page, date, departure_time, number_of_ticket):
    """Fill all form fields with error handling"""
    await safe_page_operation(lambda: fill_date_field(page, date))
    await safe_page_operation(lambda: fill_time_field(page, departure_time))
    await safe_page_operation(lambda: fill_ticket_count_field(page, number_of_ticket))
    logging.info(f"Form filled: date={date}, time={departure_time}, tickets={number_of_ticket}")

async def _set_select_value(page, element_id, value, label):
    """Set a select dropdown value using JS with select_option fallback"""
    try:
        await page.evaluate(f"""
            () => {{
                const select = document.getElementById('{element_id}');
                if (!select) return;
                select.value = '{value}';
                const options = select.querySelectorAll('option');
                options.forEach(option => option.removeAttribute('selected'));
                const target = select.querySelector('option[value="{value}"]');
                if (target) target.setAttribute('selected', 'selected');
            }}
        """)
    except Exception as e:
        logging.warning(f"JS set failed for {label}, trying fallback: {e}")
        try:
            el = await page.get_elements_by_css_selector(f"#{element_id}")
            if el:
                await el[0].select_option(value)
        except Exception as e2:
            raise TicketAutomationError(f"{label} selection failed: {e2}")

async def fill_date_field(page, date):
    await _set_select_value(page, 'dptDt', date, 'Date')

async def fill_time_field(page, departure_time):
    await _set_select_value(page, 'dptTm', departure_time, 'Time')

async def fill_ticket_count_field(page, number_of_ticket):
    await _set_select_value(page, 'psgInfoPerPrnb1', number_of_ticket, 'Ticket count')

async def handle_session_expiry(page, date, departure_time, number_of_ticket, departure, arrival):
    """Detect if session expired and auto-login if needed. Returns True if re-login happened."""
    page_state = await page.evaluate("""
        () => {
            const url = window.location.href;
            // Explicitly on the login page
            if (url.includes('login') || url.includes('Login')) return 'login';
            if (document.querySelector('.loginSubmit')) return 'login';

            // On the search page — check if actually logged in
            // Look for logout link/button or "로그아웃" text which only appears when logged in
            const logoutLink = document.querySelector('a[href*="logout"], a[href*="Logout"]');
            const memberInfo = document.querySelector('.login_info, .member_info, .gnb_login .login_after');
            const bodyText = document.body ? document.body.innerText : '';
            const hasLogoutText = bodyText.includes('로그아웃');
            const hasLoginText = bodyText.includes('로그인') && !hasLogoutText;
            const isLoggedIn = !!(logoutLink || memberInfo || hasLogoutText);

            if (document.getElementById('dptDt') !== null) {
                return isLoggedIn ? 'search_logged_in' : 'search_not_logged_in';
            }
            return 'unknown';
        }
    """)

    if page_state == 'search_logged_in':
        return False

    if page_state == 'search_not_logged_in':
        logging.warning("Not logged in — navigating to login page")
        await page.evaluate("""
            () => { window.location.href = 'https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=TK0701000000'; }
        """)
        await asyncio.sleep(3)
        # Fall through to login handling below

    # Re-check if we're now on the login page
    on_login_page = await page.evaluate("() => !!document.querySelector('.loginSubmit')")
    if page_state == 'login' or on_login_page:
        logging.warning("Session expired — auto-login triggered")

        # Click the login submit button (credentials are auto-filled by Chrome)
        login_btn = await page.get_elements_by_css_selector("input.loginSubmit")
        if login_btn:
            await login_btn[0].click()
            logging.info("Clicked login button, waiting for redirect...")
            await asyncio.sleep(5)

            # Navigate back to the search page
            await page.evaluate("""
                () => { window.location.href = 'https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000'; }
            """)
            await asyncio.sleep(3)

            # Re-fill the form
            await fill_cities(page, departure, arrival)
            await fill_form_fields(page, date, departure_time, number_of_ticket)
            logging.info("Re-login complete, form re-filled")
            return True
        else:
            logging.error("On login page but could not find login button")
            send_notification(
                title="Login Required",
                message="Auto-login failed. Please log in manually.",
                sound="Basso"
            )
            raise TicketAutomationError("Auto-login failed — login button not found")

    # Unknown page — try navigating back to search
    logging.warning(f"On unexpected page (state={page_state}), navigating back to search")
    await page.evaluate("""
        () => { window.location.href = 'https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000'; }
    """)
    await asyncio.sleep(3)
    await fill_cities(page, departure, arrival)
    await fill_form_fields(page, date, departure_time, number_of_ticket)
    return True


async def continuous_ticket_search(page, date, departure_time, number_of_ticket, departure, arrival, include_first_class, max_arrival=None):
    """Continuous ticket checking loop with error handling"""
    attempt = 1
    consecutive_errors = 0
    max_consecutive_errors = 5

    while True:
        try:
            # Check if we're still on the right page / session is alive
            re_logged_in = await handle_session_expiry(
                page, date, departure_time, number_of_ticket, departure, arrival
            )
            if re_logged_in:
                logging.info("Session restored, resuming search")

            await safe_page_operation(lambda: click_search_button(page))
            await asyncio.sleep(3)

            tickets_found = await safe_page_operation(lambda: check_for_tickets(page, include_first_class, max_arrival))

            if tickets_found:
                break

            await safe_page_operation(lambda: refill_form_after_search(page, date, departure_time, departure, arrival))

            # Log every 10 attempts to avoid spam
            if attempt % 10 == 0:
                logging.info(f"Search attempt #{attempt} — no tickets yet")

            attempt += 1
            consecutive_errors = 0

        except Exception as e:
            consecutive_errors += 1
            logging.error(f"Attempt #{attempt} error ({consecutive_errors}/5): {e}")

            if consecutive_errors >= max_consecutive_errors:
                raise TicketAutomationError(f"Too many consecutive errors: {consecutive_errors}")

            await asyncio.sleep(5)
            attempt += 1

async def click_search_button(page):
    """Click the search button with error handling"""
    search_button = await page.get_elements_by_css_selector("input[type='submit']")
    if search_button:
        await search_button[0].click()
    else:
        raise TicketAutomationError("Search button not found")

async def check_for_tickets(page, include_first_class=False, max_arrival=None):
    """Check for available tickets and handle ticket booking.

    Checks these columns per row:
      - td[7]: 일반실 (always)
      - td[8]: 예약대기 (always)
      - td[6]: 특실 (only if include_first_class is True)

    If max_arrival is set (e.g. "1200"), skips rows where arrival time > max_arrival.
    Arrival time is in td[5] as <em class="time">HH:MM</em>.
    """
    columns_js = "[7, 8"
    if include_first_class:
        columns_js += ", 6"
    columns_js += "]"

    max_arrival_int = int(max_arrival) if max_arrival else 0
    column_labels = {6: "특실", 7: "일반실", 8: "예약대기"}

    try:
        result = await page.evaluate(f"""
            () => {{
                const columns = {columns_js};
                const maxArrival = {max_arrival_int};
                const rows = document.querySelectorAll('#result-form tbody tr');
                const available = [];
                const skipped = [];

                for (const row of rows) {{
                    const tds = row.querySelectorAll('td');
                    if (tds.length < 9) continue;

                    // Extract arrival time from td[5] (0-indexed: tds[4])
                    if (maxArrival > 0) {{
                        const arrivalEl = tds[4] ? tds[4].querySelector('em.time') : null;
                        if (arrivalEl) {{
                            const arrivalTime = parseInt(arrivalEl.textContent.replace(':', ''), 10);
                            if (arrivalTime > maxArrival) {{
                                skipped.push(arrivalEl.textContent.trim());
                                continue;
                            }}
                        }}
                    }}

                    // Check columns in priority order for this row
                    for (const col of columns) {{
                        const td = tds[col - 1];
                        if (!td) continue;
                        const link = td.querySelector('a');
                        if (link && link.textContent && link.textContent.includes('예약하기')) {{
                            available.push({{col: col, rowIndex: row.rowIndex}});
                        }}
                    }}
                }}
                return {{available: available, skipped: skipped}};
            }}
        """)

        import json
        try:
            if isinstance(result, str):
                result = json.loads(result)

            skipped = result.get('skipped', [])
            if skipped:
                logging.debug(f"Skipped trains arriving at: {', '.join(skipped)} (after {max_arrival[:2]}:{max_arrival[2:]})")

            available = result.get('available', [])
            if len(available) > 0:
                # Click the first match (already in priority order: 일반실 > 예약대기 > 특실)
                target = available[0]
                target_row = target['rowIndex']
                target_col = target['col']

                click_result = await page.evaluate(f"""
                    () => {{
                        const rows = document.querySelectorAll('#result-form tbody tr');
                        for (const row of rows) {{
                            if (row.rowIndex === {target_row}) {{
                                const tds = row.querySelectorAll('td');
                                const td = tds[{target_col} - 1];
                                if (td) {{
                                    const link = td.querySelector('a');
                                    if (link) {{ link.click(); return true; }}
                                }}
                            }}
                        }}
                        return false;
                    }}
                """)

                if isinstance(click_result, str):
                    click_result = json.loads(click_result)

                if click_result:
                    col_label = column_labels.get(target_col, 'unknown')
                    logging.info(f"🎉 TICKET FOUND! Clicked [{col_label}]")
                    await handle_ticket_found()
                    return True
        except Exception as parse_error:
            logging.error(f"Error parsing results: {parse_error}")

    except Exception as e:
        logging.error(f"Ticket check failed: {e}")

    return False

async def handle_ticket_found():
    """Handle notification when ticket is found"""
    recipient = os.getenv("NOTIFY_EMAIL", "")
    if recipient:
        email_success = False
        # Try SMTP first (cross-platform)
        email_success = send_email_smtp(
            to_email=recipient,
            subject="Ticket Found (SRT) - Buy within 10 minutes",
            message="Hello from ticketing automation, buy within 10 minutes",
        )
        # Fallback to AppleScript on macOS
        if not email_success and platform.system() == "Darwin":
            try:
                from send_email import send_email
                email_success = send_email(
                    to_email=recipient,
                    subject="Ticket Found (SRT) - Buy within 10 minutes",
                    message="Hello from ticketing automation, buy within 10 minutes",
                )
            except Exception:
                pass
        if email_success:
            logging.info("✓ Email sent")
        else:
            logging.error("✗ Email failed")
    else:
        logging.warning("NOTIFY_EMAIL not set — skipping email notification")
    
    send_notification(
        title="Ticket Found!",
        message="Buy within 10 minutes",
        sound="Frog"
    )

    # Send Telegram notification via openclaw (fire-and-forget, don't block booking)
    try:
        subprocess.Popen(
            [
                "openclaw", "tui",
                "--session", "srt-ticket",
                "--message", "Send a Telegram message to Jaeyun saying: ✅ We got the SRT train ticket. Buy within 10 minutes!"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logging.info("✓ Telegram notification dispatched via openclaw")
    except Exception as e:
        logging.error(f"✗ Failed to send Telegram notification: {e}")

async def refill_form_after_search(page, date, departure_time, departure, arrival):
    """Re-fill the form after search results"""
    # Quick check: are we still on the search page?
    on_search_page = await page.evaluate("() => document.getElementById('dptRsStnCdNm') !== null")
    if not on_search_page:
        logging.warning("Not on search page during refill — session may have expired")
        raise TicketAutomationError("Not on search page during refill")

    # Re-fill departure and destination cities
    departure_city = await page.get_elements_by_css_selector("#dptRsStnCdNm")
    destination_city = await page.get_elements_by_css_selector("#arvRsStnCdNm")

    if departure_city and destination_city:
        await departure_city[0].fill(departure, clear_existing=True)
        await destination_city[0].fill(arrival, clear_existing=True)
    # Re-select date and departure_time after refresh
    try:
        await page.evaluate(f"""
            () => {{
                const dptDt = document.getElementById('dptDt');
                const dptTm = document.getElementById('dptTm');
                if (dptDt) dptDt.value = '{date}';
                if (dptTm) dptTm.value = '{departure_time}';
            }}
        """)
    except Exception as e:
        logging.error(f"Form refill failed: {e}")
        raise TicketAutomationError("Form refill failed")

if __name__ == "__main__":
    asyncio.run(main(date="20251003", departure_time="200000", number_of_ticket="2", departure="동대구", arrival="수서"))
    # asyncio.run(handle_ticket_found())
