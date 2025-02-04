import requests
# from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging
import sys
import platform
import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL to scrape
# url = "https://www.stubhub.com/harry-potter-and-the-cursed-child-new-york-tickets-11-27-2024/event/153276708/?clickref=1011lzXHEjEc&utm_source=partnerize_calebsiegel&utm_medium=publisher_program&utm_sub_medium=Comparison%2FReview&utm_campaign=1101l799&utm_content=0&PCID=partnerize_all&quantity=0"
# url = 'https://www.stubhub.com/swept-away-new-york-tickets-11-30-2024/event/153796970/?clickref=1011lzXHFHPh&utm_source=partnerize_calebsiegel&utm_medium=publisher_program&utm_sub_medium=Comparison%2FReview&utm_campaign=1101l799&utm_content=0&PCID=partnerize_all&quantity=0'

def get_chrome_options():
    """Configure Chrome options for headless scraping with optimizations."""
    options = webdriver.ChromeOptions()
    
    # Basic setup
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Performance optimizations
    performance_args = [
        "--disable-gpu",
        "--disable-images",
        "--blink-settings=imagesEnabled=false",
        "--disable-animations",
        "--disable-extensions",
        "--disable-notifications",
        "--disable-geolocation",
        "--disable-infobars",
        "--disable-web-security",
        "--disable-site-isolation-trials",
        "--ignore-certificate-errors",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding"
    ]
    for arg in performance_args:
        options.add_argument(arg)
    
    # Browser identification
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.page_load_strategy = 'eager'
    
    return options

def setup_driver():
    """Set up and configure the Chrome WebDriver."""
    options = get_chrome_options()
    base_path = ChromeDriverManager().install()
    chrome_driver_path = base_path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
    
    service = Service(executable_path=chrome_driver_path, port=9515)
    os.chmod(chrome_driver_path, 0o755)
    service.start()
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(15)
    driver.set_script_timeout(15)
    
    # Set headers
    driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
        'headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    })
    
    return driver

def wait_for_content(driver):
    """Wait for page content to load and be accessible."""
    # Wait for app element and document complete
    WebDriverWait(driver, 5).until(
        EC.all_of(
            EC.presence_of_element_located((By.ID, "app")),
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    )
    
    # Wait for price or sort elements
    try:
        WebDriverWait(driver, 5).until(
            EC.any_of(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '$')]")),
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Sort by price')]"))
            )
        )
    except Exception:
        logger.warning("Timeout waiting for price elements")
    
    time.sleep(0.5)  # Short wait for final render

def extract_ticket_info(raw_text, listings=None):
    """Extract ticket information from page content."""
    # Try extracting from "Sort by price" split
    split_text = raw_text.split("Sort by price", 1)
    if len(split_text) > 1:
        content = split_text[1].strip().split("\n\n")[0].split("\n")
        start_index = 1 if content[0].lower().strip() == "no image available" else 0
        price_line = next((line for line in content if line.startswith("$")), "")
        
        return {
            "location": content[start_index].strip(),
            "row": content[start_index + 1].strip(),
            "quantity": content[start_index + 2].split()[0],
            "note": "",
            "price": price_line.strip()
        }
    
    # Fallback to direct listing extraction
    if listings and len(listings) > 0:
        listing_text = listings[0].text.split('\n')
        price_line = next((line for line in listing_text if line.startswith("$")), "")
        
        return {
            "location": listing_text[0].strip() if len(listing_text) > 0 else "Unknown",
            "row": listing_text[1].strip() if len(listing_text) > 1 else "Unknown",
            "quantity": listing_text[2].split()[0] if len(listing_text) > 2 else "1",
            "note": "",
            "price": price_line.strip()
        }
    
    return None

def scrape_with_selenium(url):
    """Main function to scrape ticket information from StubHub."""
    start_time = time.time()
    driver = None
    
    try:
        driver = setup_driver()
        logger.info(f'Starting page navigation to: {url}?quantity=0')
        
        # Navigate and wait for content
        driver.get(f"{url}?quantity=0")
        wait_for_content(driver)
        
        # Extract content
        app_element = driver.find_element(By.ID, "app")
        raw_text = app_element.text
        listings = driver.find_elements(By.XPATH, "//div[contains(@class, 'listing')] | //div[contains(@class, 'ticket')]")
        
        # Extract and return ticket info
        ticket_info = extract_ticket_info(raw_text, listings)
        if ticket_info:
            logger.info(f'Extracted ticket info: {ticket_info}')
            logger.info(f'Total scrape completed in {time.time() - start_time:.2f} seconds')
            return ticket_info
        
        logger.warning("No ticket information found")
        return None
        
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}", exc_info=True)
        return None
    finally:
        if driver:
            driver.quit()