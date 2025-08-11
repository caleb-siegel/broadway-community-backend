import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models import Token, Event_Info, Event_Alert, Category_Alert, Event, Venue, Region
from db import db
import sendgrid
from sendgrid.helpers.mail import Mail
from sqlalchemy.orm import joinedload
from collections import defaultdict
from stubhub_scraper import scrape_with_api
from twilio.rest import Client
import logging
import pytz
from decimal import Decimal
import math
from notifications import alert_notification

# Set up logger
logger = logging.getLogger(__name__)

# Load the .env file if present (for local development)
load_dotenv()

client_id = os.getenv('STUBHUB_CLIENT_ID')
client_secret = os.getenv('STUBHUB_CLIENT_SECRET')
sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')

############# Retrieving Stubhub Data #############
# Partnerize Affiliate Link
partnerize_tracking_link = "https://stubhub.prf.hn/click/camref:1100lTenp/destination:"

# function to call stubhub using authentication info to get access token
def token_request():
    url = 'https://account.stubhub.com/oauth2/token'
    auth = (client_id, client_secret)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'client_credentials', "scope": "read:events"}
    
    response = requests.post(url, headers=headers, data=data, auth=auth)
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data
    else:
        raise Exception(f'Failed to obtain token: {response.status_code}, {response.text}')

# function to get the access token and update database with info
def get_stubhub_token(client_id, client_secret):
    token = Token.query.first()
    current_time = datetime.now() - timedelta(hours=5)
    
    # only generate a new token if the old one expired
    if token != None and token.expires_at > current_time:
        return token.access_token
    
    else:
        received_token_data = token_request()
        access_token = received_token_data["access_token"]
        expires_at = current_time + timedelta(seconds=received_token_data["expires_in"])
        
        # if there are no token instances, create one
        if token == None:
            new_token = Token(access_token=access_token, expires_at=expires_at)
            db.session.add(new_token)
            db.session.commit()
        
        # if the token is expired, generate a new one
        elif token.expires_at < current_time:
            token.access_token = access_token
            token.expires_at = expires_at
            db.session.commit()

# function to create the link to call stubhub's api with given certain parameters
def get_category_link(category_id, updated_at="", latitude="", longitude="", max_distance=1000):
    # add starting point
    link = "https://api.stubhub.net/catalog/categories/"
    
    # add categoryId
    link = link + category_id + "/events"
    
    # add parking pass filter
    link = link + "?exclude_parking_passes=true"
    
    # add lat/long/distance
    if latitude and longitude:
        link = link + f"&latitude={latitude}&longitude={longitude}&max_distance_in_meters={max_distance}"
    
    # add updated_since
    # link = link + "&updated_since=" + str(updated_at)

    return link

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
    
# function to use the received data to find the cheapest ticket in the category
def find_cheapest_ticket(events, start_date=datetime.now().isoformat(), end_date=None):    
    cheapest_ticket = None
    current_time = datetime.now(datetime.fromisoformat('2024-01-01T00:00:00-05:00').tzinfo)  # Eastern Time
    
    # Check if there are any events to process
    if not events["_embedded"]["items"]:
        return None
    
    for event in events["_embedded"]["items"]:
        min_ticket_price = event["min_ticket_price"]
        
        # Skip events without a valid ticket price
        if min_ticket_price is None:
            continue

        within_date_range = True
        
        # Get and format the event date
        event_date_str = event["start_date"]
        
        if not event_date_str:
            continue
        
        # Parse the ISO 8601 datetime string
        event_datetime = datetime.fromisoformat(event_date_str)
        event_date = event_datetime.date()

        if start_date or end_date:
            # Determine if the event date is within the specified range
            start_date_formatted = datetime.fromisoformat(start_date).date()
            
            if event_date < start_date_formatted:
                within_date_range = False
            if end_date:
                end_date_formatted = datetime.fromisoformat(end_date).date()
                if event_date > end_date_formatted:
                    within_date_range = False
        
        try:
            # Skip if show has already started
            if event_datetime <= current_time:
                continue
            
        except ValueError:
            # Skip this event if the date format is incorrect
            print(f"Skipping event due to invalid date format: {event_date_str}")
            continue

        # Update the cheapest ticket if within range and price is lower
        if within_date_range:
            ticket_price_amount = min_ticket_price["amount"]
            if ticket_price_amount is not None:
                if cheapest_ticket is None or ticket_price_amount < cheapest_ticket["min_ticket_price"]["amount"]:
                    cheapest_ticket = event
    
    return cheapest_ticket

# function to call stubhub and update the database with the new data
def fetch_stubhub_data(events):
    try:
        token = get_stubhub_token(client_id, client_secret)
    except Exception as e:
        logger.error(f"Failed to get Stubhub token: {str(e)}")
        return {"error": "Authentication failed with Stubhub API"}, 401
    
    if not events:
        logger.warning("No events provided to fetch_stubhub_data")
        return {"error": "No events provided"}, 404

    event_data = []
    for event in events:
        try:
            # Skip closed events
            if event.closed:
                logger.info(f"Skipping closed event: {event.name} (ID: {event.id})")
                continue

            # if there is no associated venue with the event, assign an empty string to lat and long values
            if event.venue:
                latitude = event.venue.latitude
                longitude = event.venue.longitude
            else:
                latitude = ""
                longitude = ""
            
            # address edge case of updated_at variable value from database
            if not event.event_info:
                updated_at = ""
            elif not event.event_info[0].updated_at:
                updated_at = ""
            else:
                updated_at = event.event_info[0].updated_at
            
            endpoint = get_category_link(event.stubhub_category_id, "", latitude, longitude, 100)
            
            try:
                events_data = get_broadway_tickets(token, endpoint)
                if not events_data:
                    logger.error(f"Failed to get data from Stubhub API for event {event.name} (ID: {event.id})")
                    continue
            except Exception as e:
                logger.error(f"API call failed for event {event.name} (ID: {event.id}): {str(e)}")
                continue
            
            if not events_data["_embedded"]["items"]:
                logger.info(f"No ticket data available for event {event.name} (ID: {event.id})")
                continue
            
            try:
                cheapest_ticket = find_cheapest_ticket(events_data)
                if not cheapest_ticket:
                    logger.info(f"No valid tickets found for event {event.name} (ID: {event.id})")
                    continue
                
                start_date = cheapest_ticket["start_date"]
                non_formatted_datetime = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S%z")
                
                non_formatted_time = non_formatted_datetime.time()
                non_formatted_date = non_formatted_datetime.date()
                non_formatted_weekday = non_formatted_datetime.weekday()
                
                formatted_time = non_formatted_datetime.strftime("%-I:%M%p").lower()
                formatted_date = non_formatted_datetime.strftime("%a, %b %-d, %Y %-I%p")
                complete_formatted_date = formatted_date[:-2] + formatted_date[-2:].lower()
                formatted_weekday = non_formatted_datetime.strftime("%a")

                old_price = 0

                # if event_info is empty
                if not event.event_info:
                    # Set current time in ET timezone
                    current_time = datetime.now() - timedelta(hours=5)
                    
                    try:
                        # post new entry
                        new_event_info = Event_Info(
                            name=cheapest_ticket["name"],
                            event_id=event.id,
                            price=round(cheapest_ticket["min_ticket_price"]["amount"]),
                            event_time=non_formatted_time,
                            event_date=non_formatted_date,
                            event_weekday=non_formatted_weekday,
                            formatted_date=complete_formatted_date,
                            sortable_date=non_formatted_datetime,
                            link=partnerize_tracking_link + cheapest_ticket["_links"]["event:webpage"]["href"],
                            average_denominator=1,
                            average_lowest_price=round(cheapest_ticket["min_ticket_price"]["amount"]),
                            updated_at=current_time,
                        )
                        db.session.add(new_event_info)

                        logger.info(f"Added new event info for {new_event_info.name}")
                        event_data.append(new_event_info.to_dict())
                        
                        if event.event_alerts:
                            alert_notification(old_price, new_event_info.price, event.name, event.event_alerts, new_event_info)
                        if event.category.category_alerts:
                            alert_notification(old_price, new_event_info.price, event.name, event.category.category_alerts, new_event_info)
                        
                    except Exception as e:
                        logger.error(f"Failed to create new event info for {event.name} (ID: {event.id}): {str(e)}")
                        db.session.rollback()
                        continue

                else:
                    try:
                        old_price = event.event_info[0].price
                        new_price = round(cheapest_ticket["min_ticket_price"]["amount"])
                        old_formatted_date = event.event_info[0].formatted_date
                        old_link = event.event_info[0].link
                        new_link = partnerize_tracking_link + cheapest_ticket["_links"]["event:webpage"]["href"]

                        if new_price == old_price and complete_formatted_date == old_formatted_date and new_link == old_link:
                            # No need to log when nothing changes
                            event_info_variable = event.event_info[0]
                            event_info_variable.updated_at = datetime.now() - timedelta(hours=5)
                            event_data.append(event.event_info[0].to_dict())
                        else:
                            # patch entry with new info
                            event_info_variable = event.event_info[0]
                            try:
                                event_info_variable.name = cheapest_ticket["name"]
                                event_info_variable.event_id = event.id
                                event_info_variable.price = new_price
                                event_info_variable.event_time = non_formatted_time
                                event_info_variable.event_date = non_formatted_date
                                event_info_variable.event_weekday = non_formatted_weekday
                                event_info_variable.formatted_date = complete_formatted_date
                                event_info_variable.sortable_date = non_formatted_datetime
                                event_info_variable.link = new_link
                                event_info_variable.updated_at = datetime.now() - timedelta(hours=5)

                                # update the average
                                new_count = event.event_info[0].average_denominator + 1
                                old_average = event.event_info[0].average_lowest_price
                                try:
                                    average = ((old_average * (new_count - 1)) + new_price) / new_count
                                except Exception as e:
                                    logger.error(f"Failed to calculate average price for {event.name} (ID: {event.id}). Values: old_avg={old_average}, new_count={new_count}, new_price={new_price}. Error: {str(e)}")
                                    raise
                                event_info_variable.average_denominator = int(new_count)
                                event_info_variable.average_lowest_price = average

                                logger.info(f"Updated {event.name}: Price ${old_price} -> ${new_price}")
                                event_data.append(event_info_variable.to_dict())
                                
                                if event.event_alerts:
                                    alert_notification(old_price, event_info_variable.price, event.name, event.event_alerts, event_info_variable)
                                if event.category.category_alerts:
                                    alert_notification(old_price, event_info_variable.price, event.name, event.category.category_alerts, event_info_variable)
                            except Exception as e:
                                logger.error(f"Failed to update event info fields for {event.name} (ID: {event.id}): {str(e)}")
                                raise

                    except Exception as e:
                        logger.error(f"Failed to update event info for {event.name} (ID: {event.id}): {str(e)}")
                        db.session.rollback()
                        continue

            except Exception as e:
                logger.error(f"Error processing ticket data for {event.name} (ID: {event.id}): {str(e)}")
                continue

        except Exception as e:
            logger.error(f"Unexpected error processing event {event.name if hasattr(event, 'name') else 'Unknown'}: {str(e)}")
            continue

        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Database commit failed: {str(e)}")
            db.session.rollback()
            return {"error": "Failed to save changes to database"}, 500

    return event_data
        
def fetch_stubhub_data_with_dates(events, start_date = None, end_date = None):
    token = get_stubhub_token(client_id, client_secret)

    if not events:
        return {"error": f"Couldn't fetch events"}, 404

    res = []
    current_time = datetime.now() - timedelta(hours=5)
    
    for event in events:
        # Skip closed events
        if event.closed:
            logger.info(f"Skipping closed event: {event.name} (ID: {event.id})")
            continue

        # if there is no associated venue with the event, assign an empty string to lat and long values
        if event.venue:
            latitude = event.venue.latitude
            longitude = event.venue.longitude
        else:
            latitude = ""
            longitude = ""
        
        # Get the most recent event info for average price calculation
        recent_event_info = None
        if event.event_info:
            recent_event_info = max(event.event_info, key=lambda x: x.updated_at if x.updated_at else datetime.min)
        
        endpoint = get_category_link(event.stubhub_category_id, "", latitude, longitude, 100)
        events_data = get_broadway_tickets(token, endpoint)
        
        if not events_data["_embedded"]["items"]:
            continue
        else:
            cheapest_ticket = find_cheapest_ticket(events_data, start_date, end_date)
            
            if cheapest_ticket is not None:
                start_date_var = cheapest_ticket["start_date"]
                non_formatted_datetime = datetime.strptime(start_date_var, "%Y-%m-%dT%H:%M:%S%z")
                formatted_date = non_formatted_datetime.strftime("%a, %b %-d, %Y %-I%p")
                complete_formatted_date = formatted_date[:-2] + formatted_date[-2:].lower()
                
                # Calculate average lowest price from recent history
                avg_lowest_price = None
                if recent_event_info and recent_event_info.price:
                    avg_lowest_price = recent_event_info.average_lowest_price
                
                # Calculate current price
                current_price = round(cheapest_ticket["min_ticket_price"]["amount"])
                
                # Calculate price difference percentage
                price_diff_percent = 0
                if avg_lowest_price and avg_lowest_price > 0:
                    price_diff_percent = ((current_price - avg_lowest_price) / avg_lowest_price) * 100
                
                cheapest_event_info = {
                    "event_info": [
                        {
                            "name": cheapest_ticket["name"],
                            "price": current_price,
                            "formatted_date": complete_formatted_date,
                            "link": partnerize_tracking_link + cheapest_ticket["_links"]["event:webpage"]["href"],
                            "updated_at": current_time.strftime("%a, %b %-d, %-I:%M %p ET"),
                            "average_lowest_price": avg_lowest_price,
                            "event_date": non_formatted_datetime.strftime("%Y-%m-%d")
                        }
                    ],
                    "id": event.id,
                    "name": event.name,
                    "category_id": event.category_id,
                    "image": event.image,
                    "venue": event.venue.to_dict() if event.venue else None
                }            
                res.append(cheapest_event_info)
    return res

############# Add new event to database #############
def find_event_id(stubhub_link):
    try:
        # Check if the URL contains the expected pattern
        if "/event/" not in stubhub_link:
            raise ValueError("Invalid Stubhub URL: missing '/event/' pattern")
        
        # Split on /event/ and take everything after it
        after_event = stubhub_link.split("/event/")[1]
        
        # Remove any trailing slashes and query parameters
        event_id = after_event.split('/')[0].split('?')[0].strip()
        
        # Verify event_id is numeric
        if not event_id.isdigit():
            raise ValueError(f"Invalid event ID format: {event_id}")
        
        return event_id

    except IndexError:
        raise ValueError("Unable to parse event ID from URL")
    except Exception as e:
        raise ValueError(f"Error processing Stubhub URL: {str(e)}")
    
def add_tracked_event(stubhub_link):
    # get event_id from stubhub_link    
    event_id = find_event_id(stubhub_link)
    
    # fetch stubhub data with endpoint of https://api.stubhub.net/catalog/events/{event_id}
    url = f"https://api.stubhub.net/catalog/events/{event_id}"
    stubhub_token = get_stubhub_token(client_id, client_secret)
    
    try:
        stubhub_data = get_broadway_tickets(stubhub_token, url)
        
        if not stubhub_data or 'error' in stubhub_data:
            raise ValueError("Event not found")

        # Get categories data
        categories = stubhub_data['_embedded']['categories']
        category_list = []
        for category in categories:
            category_list.append({
                "name": category["name"],
                "id": category["id"]
            })
        
        # Get venue data
        venue = stubhub_data['_embedded']['venue']
        
        # Return structured response with event name
        return {
            "name": stubhub_data.get('name', ''),
            "categories": category_list,
            "venue": venue
        }
    except Exception as e:
        raise ValueError("Event not found")

def prices_by_region(region):
    # Get all venues in a region
    venues = Venue.query.filter(
        Venue.region.has(Region.name == region),
    ).all()
    
    print(venues)
    
    token = get_stubhub_token("4XWc10UmncVBoHo3lT8b", "sfwKjMe6h1cApxw1Ca7ZKTsaoa2gSRov5ECYkM2pVXEvAUW0Ux0KViQZwWfI")
    
    res = []
    
    for venue in venues:
        
        if not venues:
            return {"error": f"Couldn't fetch venues"}, 404

        
        # current_time = datetime.now() - timedelta(hours=5)
        endpoint = "https://api.stubhub.net/catalog/events/search?exclude_parking_passes=true&q=" + venue.name
        events_data = get_broadway_tickets(token, endpoint)
        
        if not events_data["_embedded"]["items"]:
            continue
        else:
            cheapest_ticket = find_cheapest_ticket(events_data)
            
            if cheapest_ticket is not None:
                start_date_var = cheapest_ticket["start_date"]
                non_formatted_datetime = datetime.strptime(start_date_var, "%Y-%m-%dT%H:%M:%S%z")
                formatted_date = non_formatted_datetime.strftime("%a, %b %-d, %Y %-I%p")
                complete_formatted_date = formatted_date[:-2] + formatted_date[-2:].lower()
                
                # Calculate current price
                current_price = round(cheapest_ticket["min_ticket_price"]["amount"])
                
                cheapest_event_info = {
                    # "event_info": [
                    #     {
                    #         "name": cheapest_ticket["name"],
                    #         "price": current_price,
                    #         "formatted_date": complete_formatted_date,
                    #         "link": partnerize_tracking_link + cheapest_ticket["_links"]["event:webpage"]["href"],
                    #         "event_date": non_formatted_datetime.strftime("%Y-%m-%d")
                    #     }
                    # ],
                    # "id": event.id,
                    "name": cheapest_ticket["name"],
                    "price": current_price,
                    # "category_id": event.category_id,
                    # "image": event.image,
                    "venue": venue.name,
                    "formatted_date": complete_formatted_date,
                    "link": partnerize_tracking_link + cheapest_ticket["_links"]["event:webpage"]["href"],
                    # "venue": venue.to_dict() if venue else None
                    }            
                # print(cheapest_event_info)
                res.append(cheapest_event_info)
    return res