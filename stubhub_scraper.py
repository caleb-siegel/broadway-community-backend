import requests
# from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import logging
import sys
import platform
import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import shutil
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL to scrape
# url = "https://www.stubhub.com/harry-potter-and-the-cursed-child-new-york-tickets-11-27-2024/event/153276708/?clickref=1011lzXHEjEc&utm_source=partnerize_calebsiegel&utm_medium=publisher_program&utm_sub_medium=Comparison%2FReview&utm_campaign=1101l799&utm_content=0&PCID=partnerize_all&quantity=0"
# url = 'https://www.stubhub.com/swept-away-new-york-tickets-11-30-2024/event/153796970/?clickref=1011lzXHFHPh&utm_source=partnerize_calebsiegel&utm_medium=publisher_program&utm_sub_medium=Comparison%2FReview&utm_campaign=1101l799&utm_content=0&PCID=partnerize_all&quantity=0'

def get_chrome_options():
    """Configure Chrome options for headless scraping with optimizations."""
    options = webdriver.ChromeOptions()
    
    # Basic setup for serverless environment
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Check if running on Vercel
    if os.environ.get('VERCEL'):
        chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/google-chrome')
        options.binary_location = chrome_bin
    
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
        "--disable-renderer-backgrounding",
        "--single-process",
        "--no-zygote"
    ]
    for arg in performance_args:
        options.add_argument(arg)
    
    # Browser identification
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.page_load_strategy = 'eager'
    
    return options

def setup_driver():
    """Set up and configure the Chrome WebDriver for serverless environment."""
    try:
        print("Setting up Chrome driver...")
        options = webdriver.ChromeOptions()
        
        # Use default Chrome binary in Vercel environment
        if os.environ.get('VERCEL'):
            print("Running in Vercel environment")
            # Use Vercel's default Chrome location
            options.binary_location = "/opt/google/chrome/chrome"
            
            # Set up ChromeDriver from the current directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            chromedriver_path = os.path.join(current_dir, "chromedriver")
            
            print(f"Chrome binary path: {options.binary_location}")
            print(f"ChromeDriver path: {chromedriver_path}")
            
            if not os.path.exists(options.binary_location):
                print(f"Warning: Chrome binary not found at {options.binary_location}")
                # Try alternative Chrome locations
                alt_locations = [
                    "/usr/bin/google-chrome",
                    "/usr/bin/google-chrome-stable"
                ]
                for loc in alt_locations:
                    if os.path.exists(loc):
                        print(f"Found Chrome at alternative location: {loc}")
                        options.binary_location = loc
                        break
            
            if not os.path.exists(chromedriver_path):
                print(f"Warning: ChromeDriver not found at {chromedriver_path}")
        
        # Add required options for running in serverless environment
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--hide-scrollbars')
        options.add_argument('--disable-extensions')
        options.add_argument('--single-process')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-dev-tools')
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--disable-background-networking')
        
        # Performance optimizations
        options.add_argument('--disable-images')
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_argument('--disable-animations')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-geolocation')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-site-isolation-trials')
        
        # Browser identification
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        # Initialize ChromeDriver with specific path in Vercel environment
        if os.environ.get('VERCEL'):
            service = Service(executable_path=chromedriver_path)
        else:
            service = Service()  # Use default for local development
            
        driver = webdriver.Chrome(service=service, options=options)
        print("Chrome driver setup completed successfully")
        return driver
        
    except Exception as e:
        print(f"Error setting up Chrome driver: {str(e)}")
        print("\nEnvironment Information:")
        print(f"VERCEL: {os.environ.get('VERCEL')}")
        print(f"PATH: {os.environ.get('PATH')}")
        print("\nSystem State:")
        try:
            print("Checking Chrome installation:")
            for chrome_path in ["/opt/google/chrome/chrome", "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"]:
                if os.path.exists(chrome_path):
                    print(f"Chrome exists at {chrome_path}")
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"\nCurrent directory contents ({current_dir}):")
            print(os.listdir(current_dir))
            
            print("\nChrome version check:")
            try:
                chrome_version = subprocess.check_output([options.binary_location, '--version'], stderr=subprocess.STDOUT)
                print(f"Chrome version: {chrome_version.decode()}")
            except Exception as e3:
                print(f"Could not get Chrome version: {str(e3)}")
                
        except Exception as e2:
            print(f"Error checking system state: {str(e2)}")
        raise

def wait_for_content(driver):
    """Wait for page content to load and be accessible."""
    # Wait for app element and document complete with shorter timeout
    WebDriverWait(driver, 3).until(
        EC.all_of(
            EC.presence_of_element_located((By.ID, "app")),
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    )
    
    # Wait for price or sort elements
    try:
        WebDriverWait(driver, 3).until(
            EC.any_of(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '$')]")),
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Sort by price')]"))
            )
        )
    except Exception:
        logger.warning("Timeout waiting for price elements")
    
    time.sleep(0.3)  # Reduced sleep for serverless

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