import requests
import logging
import time
from datetime import datetime, timedelta
from collections import defaultdict
from stubhub_scraper import scrape_with_selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys


client_id = "4XWc10UmncVBoHo3lT8b"
client_secret = "sfwKjMe6h1cApxw1Ca7ZKTsaoa2gSRov5ECYkM2pVXEvAUW0Ux0KViQZwWfI"

# scrape function

def old_scrape_with_selenium(url):

    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no browser window)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Open the StubHub page
    driver.get(url)

    # Allow the page to load
    driver.implicitly_wait(10)

    # Extract the content (e.g., ticket details)
    try:
        ticket_info = driver.find_element(By.ID, "listings-container").text  # Replace with appropriate selector
        print(ticket_info)
        
        # split_text = ticket_info.split("Sort by price", 1)
        # if len(split_text) > 1:
        #     # Extract the text directly after "sort by price"
        #     content_after_sort_by_price = split_text[1].strip()

        #     # Find the ending point at the word "Lowest price"
        #     end_index = content_after_sort_by_price.find("Lowest price")
        #     if end_index > -1:
        #         result = content_after_sort_by_price[:end_index].strip()  # Slice up to "Lowest price"

        #         # Split the extracted result into lines
        #         lines = result.split("\n")

        #         # Create a dictionary with keys as "line_1", "line_2", etc.
        #         extracted_object = {
        #             "location": lines[0].strip(),  # First line: location (section)
        #             "row": lines[1].strip(),       # Second line: row (Row info)
        #             "quantity": lines[2].strip()[0],  # Third line: quantity (tickets count)
        #             "note": lines[3].strip(),   # Fourth and onward can be joined for notes if needed
        #             "price": lines[4].strip()      # Fifth line: price
        #         }

        #         return extracted_object
        #     else:
        #         print("The phrase 'Lowest price' was not found in the text after 'sort by price'.")
        # else:
        #     print("The phrase 'sort by price' was not found in the text.")
        
    except Exception as e:
        print(f"Error: {e}")

    # Close the driver
    driver.quit()
    
def scrape_with_selenium(url, max_attempts=100):
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Set up Selenium WebDriver with enhanced options
    options = webdriver.ChromeOptions()
    # Remove headless to see what's happening
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1200")  # Larger viewport
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # Open the StubHub page
        driver.get(url)
        
        # Wait for the initial listings container to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "listings-container"))
        )
        
        # Initialize variables for tracking
        last_line_count = 0
        no_progress_count = 0
        
        # Scroll and load strategy
        for attempt in range(max_attempts):
            # Get the listings container
            try:
                listings_container = driver.find_element(By.ID, "listings-container")
                
                # Extreme scrolling techniques
                # 1. Page Down key multiple times
                for _ in range(5):
                    ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform()
                    time.sleep(0.5)
                
                # 2. Scroll to bottom using JavaScript
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # 3. Scroll in small increments
                driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"Error finding listings container: {e}")
                break
            
            # Try to find and click "Load More" buttons
            try:
                load_more_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Load More') or contains(text(), 'Show More') or contains(@class, 'load-more')]")
                for button in load_more_buttons:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(0.5)
                        button.click()
                        time.sleep(2)
                    except Exception as btn_error:
                        logger.warning(f"Error clicking load more button: {btn_error}")
            except Exception as load_more_error:
                logger.info("No load more buttons found")
            
            # Check current state of listings
            current_listings_text = listings_container.text
            current_lines = current_listings_text.split('\n')
            
            # Log progress
            logger.info(f"Attempt {attempt+1}: Found {len(current_lines)} lines")
            
            # Check if we're making progress
            if len(current_lines) > last_line_count:
                last_line_count = len(current_lines)
                no_progress_count = 0
            else:
                no_progress_count += 1
            
            # Stop if we've made no progress for several attempts
            if no_progress_count >= 10:
                break
        
        # Final extraction
        listings_container = driver.find_element(By.ID, "listings-container")
        all_listings_text = listings_container.text
        individual_listings = all_listings_text.split('\n')
        
        logger.info(f"FINAL Total number of text lines: {len(individual_listings)}")
        
        # Optional: Save full page source for debugging
        with open('stubhub_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        return all_listings_text, individual_listings
    
    except Exception as e:
        logger.error(f"Overall error extracting listings text: {e}")
        return None, None
    
    finally:
        # Always close the driver
        driver.quit()

# function to use the token and created endpoint to get the stubhub data
def get_broadway_tickets(token, endpoint):
    url = endpoint
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Failed to fetch tickets from {url}: {response.status_code}, {response.text}')
        return None
    
token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOjEzMDQsImlhdCI6MTczMzMzMTM0Mywic2NvcGUiOiJyZWFkOmV2ZW50cyIsInQiOjAsInZnZy1zdiI6ImVjOTM2OWQ2YzA3NjQ5YzQ5NTI4N2RlOWQ2MDA5MDhlIiwiZXhwIjoxNzMzNDE3NzQzLCJhdXRoLXR5cGUiOjEsImFndCI6IjlDTUYyUW5NL0orWEpaRWJQZC9KK2RObHVhTytralR6Q2RJajFoUVVnQ2c9In0.FI8DsJwtmVfKYMvPZTA72R5x58fatDwKXb8Hzx9nLP13ITvClByqZqNGgRIUsPUa9t945-0eIDMeJKp0dk7PRsXric0VHnbwPadDPmc2rpTAKK6N-msgMbMfFRoiud9pbyQ7lGkncxzBWvD5ohI7F8bzuyDojNLCYGAqsxjbsngprT1rqxgCq-Qlxjgzbm8TvAWa6YQSLD6rMHz-_ZATVZRS0iQ6gMWu1Hf7rYoj6nc5pX-l4uxo3Gwt_6Q-VqiZV_gVzP-2Oacz1YXMYxTTqlO78sUJBqichjaeV5UZNubp_oIa7Mf3lzP0v_xnnc7hsSgTUX_MDpwDl8knt-74Dw"

# If we are only fetching one event, scrape the site to find the ticket info
# if len(events) == 1:
    # add_scraped_data = True

endpoint = "https://api.stubhub.net/catalog/categories/6639/events?exclude_parking_passes=true&latitude=40.7505621&longitude=-73.9934709&max_distance_in_meters=100"
events_data = get_broadway_tickets(token, endpoint)

events = []
links = []

for i, event in enumerate(events_data["_embedded"]["items"]):
    date_str = event["start_date"]
    date = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")

    if (date.month < 3) and (date.weekday() not in (4, 5)) and (not (date.month == 12 and date.day == 25)) and (not (date.month == 1 and date.day == 1)):
        # print(f'{i}.{event["start_date"]} & {event["min_ticket_price"]["amount"]}')
        ref = f'https://stubhub.prf.hn/click/camref:1100lTenp/destination:{event["_links"]["event:webpage"]["href"]}'
        links.append(ref)
        events.append(event)

# for i, link in enumerate(links):
#     print(f'{i+1}.{link}')

for i, event in enumerate(events):
    start_date = event["start_date"]
    non_formatted_datetime = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S%z")
    
    non_formatted_time = non_formatted_datetime.time()
    non_formatted_date = non_formatted_datetime.date()
    non_formatted_weekday = non_formatted_datetime.weekday()
    
    formatted_time = non_formatted_datetime.strftime("%-I:%M%p").lower()
    formatted_date = non_formatted_datetime.strftime("%a, %b %-d, %Y %-I%p")
    complete_formatted_date = formatted_date[:-2] + formatted_date[-2:].lower()

    url = f'https://stubhub.prf.hn/click/camref:1100lTenp/destination:{event["_links"]["event:webpage"]["href"]}?quantity=3'
    if i == 0:
        print(url)
        print(scrape_with_selenium(url))
    # print(f'{i+1}. {complete_formatted_date}')



