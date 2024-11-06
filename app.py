from flask import Flask, make_response, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import dotenv_values, load_dotenv
from flask_bcrypt import Bcrypt
import json
import random
from datetime import datetime, timedelta
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import os
from db import db, app

# Load the .env file if present (for local development)
load_dotenv()

app.secret_key = os.getenv('FLASK_SECRET_KEY')
CORS(app, supports_credentials=True)

bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

client_id = os.getenv('STUBHUB_CLIENT_ID')
client_secret = os.getenv('STUBHUB_CLIENT_SECRET')

from models import User, Event, Event_Preference, Category_Preference, Event_Info, Category, Token, Venue

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
        
        if not events_data["_embedded"]["items"]:
            continue
        else:
            cheapest_ticket = find_cheapest_ticket(events_data)

            start_date = cheapest_ticket["start_date"]
            non_formatted_datetime = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S%z")
            
            non_formatted_time = non_formatted_datetime.time()
            non_formatted_date = non_formatted_datetime.date()
            non_formatted_weekday = non_formatted_datetime.weekday()
            
            formatted_time = non_formatted_datetime.strftime("%-I:%M%p").lower()
            formatted_date = non_formatted_datetime.strftime("%a, %b %-d, %Y %-I%p")
            complete_formatted_date = formatted_date[:-2] + formatted_date[-2:].lower()
            formatted_weekday = non_formatted_datetime.strftime("%a")

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
                    )
                    db.session.add(new_event_info)

                    print(f"tickets for {new_event_info.name} added to the database")
                    # db.session.commit()
            # if database price is lower than the scraped stubhub minimum price
            # elif round(cheapest_ticket["min_ticket_price"]["amount"]) > event.event_info[0].price:
            #     print(f'since the scraped cheapest ticket ({round(cheapest_ticket["min_ticket_price"]["amount"])}) isnt less than the old cheapest ticket ({event.event_info[0].price}, we arent changing anything)')
            #     continue
            else:
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

            db.session.commit()
        
# scheduler = BackgroundScheduler()
# scheduler.add_job(fetch_stubhub_data, 'interval', minutes=15)
# scheduler.start()

############# Notifications #############
# loop over event_preferences
def send_notification():
    preferences = db.session.query(Event_Preference).all()
    for preference in preferences:
        # if show equals show and price is below current price
        if preference.event.event_info[0].price <= preference.price:
            # send notification
            pass

############# Routes #############
@app.route("/")
def root():
    return "<h1>Welcome to the simple json server<h1>"

@app.get('/api/check_session')
def check_session():
    user = db.session.get(User, session.get('user_id'))
    print(f'check session {session.get("user_id")}')
    if user:
        return user.to_dict(rules=['-password_hash']), 200
    else:
        return {"message": "No user logged in"}, 401

@app.delete('/api/logout')
def logout():
    session.pop('user_id')
    return { "message": "Logged out"}, 200

@app.post('/api/login')
def login():
    print('login')
    data = request.json
    user = User.query.filter(User.email == data.get('email')).first()
    if user and bcrypt.check_password_hash(user.password_hash, data.get('password')):
        session["user_id"] = user.id
        print("success")
        return user.to_dict(), 200
    else:
        return { "error": "Invalid username or password" }, 401
    
@app.route('/api/user', methods=['GET', 'POST'])
def user():
    if request.method == 'GET':
        users = [user.to_dict() for user in User.query.all()]
        return make_response( users, 200 )
    
    elif request.method == 'POST':
        data = request.json
        try:
            new_user = User(
                first_name = data.get("first_name"),
                last_name = data.get("last_name"),
                email = data.get("email"),
                phone_number = data.get("phone_number"),
                password_hash = bcrypt.generate_password_hash(data.get("password_hash")).decode('utf-8')
            )
            db.session.add(new_user)
            db.session.commit()
            
            return new_user.to_dict(), 201
        except Exception as e:
            print(e)
            return {"error": f"could not post user: {e}"}, 405
    
@app.route('/api/events', methods=['GET', 'POST'])
def get_events():
    if request.method == 'GET':
        events = []
        for event in Event.query.all():
            event_dict = event.to_dict()
            events.append(event_dict)

        response = make_response(events,200)

        return response

@app.route('/api/event_preferences', methods=['GET', 'POST'])
def get_event_preferences():
    if request.method == 'GET':
        event_preferences = []
        for preference in Event_Preference.query.all():
            preference_dict = preference.to_dict()
            event_preferences.append(preference_dict)

        response = make_response(event_preferences,200)

        return response

@app.route('/api/categories', methods=['GET', 'POST'])
def get_categories():
    if request.method == 'GET':
        categories = []
        for category in Category.query.order_by(Category.id.desc()).all():
            category_dict = category.to_dict()
            categories.append(category_dict)

        response = make_response(categories,200)

        return response
    
@app.route('/api/categories/<string:name>', methods=['GET', 'POST'])
def get_category_by_name(name):
    category = db.session.query(Category).filter_by(name=name).first()
    return category.to_dict()

@app.route('/api/fetch_tickets', methods=['POST'])
def refresh_stubhub_data():
    try:
        events = db.session.query(Event).all()
        fetch_stubhub_data(events)
        return {"message": "StubHub data fetched successfully"}, 200
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(debug=True)