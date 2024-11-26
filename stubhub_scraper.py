import requests
# from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# URL to scrape
# url = "https://www.stubhub.com/harry-potter-and-the-cursed-child-new-york-tickets-11-27-2024/event/153276708/?clickref=1011lzXHEjEc&utm_source=partnerize_calebsiegel&utm_medium=publisher_program&utm_sub_medium=Comparison%2FReview&utm_campaign=1101l799&utm_content=0&PCID=partnerize_all&quantity=0"
# url = 'https://www.stubhub.com/swept-away-new-york-tickets-11-30-2024/event/153796970/?clickref=1011lzXHFHPh&utm_source=partnerize_calebsiegel&utm_medium=publisher_program&utm_sub_medium=Comparison%2FReview&utm_campaign=1101l799&utm_content=0&PCID=partnerize_all&quantity=0'

def scrape_with_beautifulsoup(url):

    # Fetch the content of the page
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
    else:
        print(f"Failed to retrieve page. Status code: {response.status_code}")

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Navigate to the deeply nested div
    nested_div = soup.body.find('div', id="app")
    if nested_div:
        for _ in range(12):  # Traverse 12 nested divs
            nested_div = nested_div.find('div') if nested_div else None
        if nested_div:
            print(nested_div.text)  # Get the text content
        else:
            print("Could not find the nested div.")
    else:
        print("App div not found.")

def scrape_with_selenium(url):

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
        ticket_info = driver.find_element(By.ID, "app").text  # Replace with appropriate selector
        # print(ticket_info)
        
        split_text = ticket_info.split("Sort by price", 1)
        if len(split_text) > 1:
            # Extract the text directly after "sort by price"
            content_after_sort_by_price = split_text[1].strip()

            # Find the ending point at the word "Lowest price"
            end_index = content_after_sort_by_price.find("Lowest price")
            if end_index > -1:
                result = content_after_sort_by_price[:end_index].strip()  # Slice up to "Lowest price"

                # Split the extracted result into lines
                lines = result.split("\n")

                # Create a dictionary with keys as "line_1", "line_2", etc.
                extracted_object = {
                    "location": lines[0].strip(),  # First line: location (section)
                    "row": lines[1].strip(),       # Second line: row (Row info)
                    "quantity": lines[2].strip()[0],  # Third line: quantity (tickets count)
                    "note": lines[3].strip(),   # Fourth and onward can be joined for notes if needed
                    "price": lines[4].strip()      # Fifth line: price
                }

                return extracted_object
            else:
                print("The phrase 'Lowest price' was not found in the text after 'sort by price'.")
        else:
            print("The phrase 'sort by price' was not found in the text.")
        
    except Exception as e:
        print(f"Error: {e}")

    # Close the driver
    driver.quit()