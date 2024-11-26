import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models import Token, Event_Info, Event_Preference, Category_Preference, Event
from db import db
import sendgrid
from sendgrid.helpers.mail import Mail
from sqlalchemy.orm import joinedload
from collections import defaultdict
from stubhub_scraper import scrape_with_selenium


# Load the .env file if present (for local development)
load_dotenv()

client_id = os.getenv('STUBHUB_CLIENT_ID')
client_secret = os.getenv('STUBHUB_CLIENT_SECRET')
sendgrid_api_key = os.getenv('SENDGRID_API_KEY')

############# Notifications #############
def events_preference_notification():
    preferences = db.session.query(Event_Preference).all()
    for preference in preferences:
        current_price = preference.event.event_info[0].price
        preference_price = preference.price
        
        if current_price <= preference_price:
            message = Mail(
                from_email='broadway.comms@gmail.com',
                to_emails=preference.user.email,
                subject=f'Price Alert: {preference.event.name} ${current_price}',
                html_content=f"""
        <strong>{preference.event.name}</strong> is selling at <strong>${current_price}</strong>.<br><br>
        
        This show is on {preference.event.event_info[0].formatted_date}.<br><br>
        
        <a href="{preference.event.event_info[0].link}">Buy the tickets here</a><br><br>

        Want to know what the view might be like from these seats? <a href="{preference.event.venue.seatplan_url}">Click here</a> and find an image from these seats.<br><br>
        
        <em>Remember that these prices don't reflect StubHub's fees, so you should expect the complete price to be around 30% higher than the amount shown above.</em>
    """
            )
            try:
                sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
                response = sg.send(message)
                print(response.status_code)
            except Exception as e:
                print(e)

def preference_notification(old_price, current_price, name, preferences, event_info):
    if preferences:
        for preference in preferences:
            preference_price = preference.price
            if current_price <= preference_price and (current_price < old_price or not old_price):
                message = Mail(
                    from_email='broadway.comms@gmail.com',
                    to_emails=preference.user.email,
                    subject=f'Price Alert: {name} ${current_price}',
                    html_content=f"""
            <strong>{name}</strong> is selling at <strong>${current_price}</strong>. It was previously selling for ${old_price} and you requested to be notified if it ever dropped below ${preference_price}<br><br>
            
            This show is on {event_info.formatted_date}.<br><br>
            
            <a href="{event_info.link}">Buy the tickets here</a><br><br>
            
            <em>Remember that these prices don't reflect StubHub's fees, so you should expect the complete price to be around 30% higher than the amount shown above.</em>
        """
                )
                try:
                    sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
                    response = sg.send(message)
                    print(response.status_code)
                except Exception as e:
                    print(e)


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
    current_time = datetime.now()
    
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
def find_cheapest_ticket(events):
    cheapest_ticket = None
    if not events["_embedded"]["items"]: 
        return None
    
    for event in events["_embedded"]["items"]:
        if event["min_ticket_price"] is None:
            continue
        else:
            min_ticket_price = event["min_ticket_price"]["amount"]
            if min_ticket_price is not None:
                if cheapest_ticket is None or min_ticket_price < cheapest_ticket["min_ticket_price"]["amount"]:
                    cheapest_ticket = event
    
    return cheapest_ticket if cheapest_ticket else "No tickets found"

# function to call stubhub and update the database with the new data
def fetch_stubhub_data(events):
    
    token = get_stubhub_token(client_id, client_secret)

    if not events:
        return {"error": f"Couldn't fetch events"}, 404
    for event in events:
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
        events_data = get_broadway_tickets(token, endpoint)
        event_data = []
        if not events_data["_embedded"]["items"]:
            continue
        else:
            cheapest_ticket = find_cheapest_ticket(events_data)
            seat_info = scrape_with_selenium(cheapest_ticket["_links"]["event:webpage"]["href"])

            start_date = cheapest_ticket["start_date"]
            non_formatted_datetime = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S%z")
            
            non_formatted_time = non_formatted_datetime.time()
            non_formatted_date = non_formatted_datetime.date()
            non_formatted_weekday = non_formatted_datetime.weekday()
            
            formatted_time = non_formatted_datetime.strftime("%-I:%M%p").lower()
            formatted_date = non_formatted_datetime.strftime("%a, %b %-d, %Y %-I%p")
            complete_formatted_date = formatted_date[:-2] + formatted_date[-2:].lower()
            formatted_weekday = non_formatted_datetime.strftime("%a")

            old_price = None

            # if event_info is empty
            if not event.event_info:
                # post new entry
                new_event_info = Event_Info (
                    name = cheapest_ticket["name"],
                    event_id = event.id,
                    price = round(cheapest_ticket["min_ticket_price"]["amount"]),
                    event_time = non_formatted_time,
                    event_date = non_formatted_date,
                    event_weekday = non_formatted_weekday,
                    formatted_date = complete_formatted_date,
                    sortable_date = non_formatted_datetime,
                    link = partnerize_tracking_link + cheapest_ticket["_links"]["event:webpage"]["href"],
                    updated_at = datetime.now(),
                    location = seat_info.location if seat_info else None,
                    row = seat_info.row if seat_info else None,
                    quantity = seat_info.quantity if seat_info else None,
                    note = seat_info.note if seat_info else None,
                )
                db.session.add(new_event_info)

                print(f"tickets for {new_event_info.name} added to the database")
                event_data.append(new_event_info.to_dict())

                preference_notification(old_price, new_event_info.price, event.name, event.event_preferences, new_event_info)
                preference_notification(old_price, new_event_info.price, event.name, event.category.category_preferences, new_event_info)
                # db.session.commit()

            # if database price is lower than the scraped stubhub minimum price
            # elif round(cheapest_ticket["min_ticket_price"]["amount"]) > event.event_info[0].price:
            #     print(f'since the scraped cheapest ticket ({round(cheapest_ticket["min_ticket_price"]["amount"])}) isnt less than the old cheapest ticket ({event.event_info[0].price}, we arent changing anything)')
            #     continue
            else:
                old_price = event.event_info[0].price
                # patch entry with new info
                event_info_variable = event.event_info[0]
                event_info_variable.name = cheapest_ticket["name"]
                event_info_variable.event_id = event.id
                event_info_variable.price = round(cheapest_ticket["min_ticket_price"]["amount"])
                event_info_variable.event_time = non_formatted_time
                event_info_variable.event_date = non_formatted_date
                event_info_variable.event_weekday = non_formatted_weekday
                event_info_variable.formatted_date = complete_formatted_date
                event_info_variable.sortable_date = non_formatted_datetime,
                event_info_variable.link = partnerize_tracking_link + cheapest_ticket["_links"]["event:webpage"]["href"]
                event_info_variable.updated_at = datetime.now()

                # print(f"tickets for {event_info_variable.id} updated successfully")
                event_data.append(event_info_variable.to_dict())

                preference_notification(old_price, event_info_variable.price, event.name, event.event_preferences, event_info_variable)
                preference_notification(old_price, event_info_variable.price, event.name, event.category.category_preferences, event_info_variable)

            db.session.commit()
    
    # events_preference_notification()

    return event_data
        
# scheduler = BackgroundScheduler()
# scheduler.add_job(fetch_stubhub_data, 'interval', minutes=15)
# scheduler.start()