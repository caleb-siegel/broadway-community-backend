import requests
import logging
import os
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_with_api(url):
    """Scrape ticket information using ScrapingBee API."""
    logger.info(f"Starting API scraping for URL: {url}")
    
    try:
        # Get API key from environment variable
        api_key = os.environ.get('SCRAPING_API_KEY')
        if not api_key:
            logger.error("API key not found in environment variables")
            return None
            
        # Configure API parameters
        params = {
            'api_key': api_key,
            'url': url,
            'render_js': 'true',       # For JavaScript-rendered content
            'premium_proxy': 'true',    # For better success rate
            'wait': '5000'             # Wait for dynamic content
        }
        
        # Make the request
        logger.info("Making API request...")
        response = requests.get(
            'https://app.scrapingbee.com/api/v1/',
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            # Parse the response
            logger.info("Successfully received response")
            content = response.text
            
            # Extract ticket information (your existing extraction logic)
            ticket_info = extract_ticket_info(content)
            if ticket_info:
                logger.info(f"Successfully extracted ticket info: {ticket_info}")
                return ticket_info
            else:
                logger.warning("No ticket information found in response")
                return None
        else:
            logger.error(f"API request failed with status code: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        return None

def extract_ticket_info(content):
    """Extract ticket information from the page content."""
    try:
        # Split at "Sort by price" as before
        split_text = content.split("Sort by price", 1)
        if len(split_text) > 1:
            content_after_sort = split_text[1].strip().split("\n\n")[0].split("\n")
            start_index = 1 if content_after_sort[0].lower().strip() == "no image available" else 0
            
            # Find the price line
            price_line = next((line for line in content_after_sort if line.startswith("$")), "")
            
            return {
                "location": content_after_sort[start_index].strip(),
                "row": content_after_sort[start_index + 1].strip(),
                "quantity": content_after_sort[start_index + 2].split()[0],
                "note": "",
                "price": price_line.strip()
            }
        return None
    except Exception as e:
        logger.error(f"Error extracting ticket info: {str(e)}")
        return None