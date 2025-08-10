from flask import Flask, make_response, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS, cross_origin
# from flask_session import Session
from dotenv import dotenv_values, load_dotenv
from flask_bcrypt import Bcrypt
from flask_session import Session
from redis import Redis
import json
from datetime import datetime, timedelta
import os
from db import db, app
from google.oauth2 import id_token
from google.auth.transport import requests
from stubhub import get_stubhub_token, fetch_stubhub_data, get_category_link, find_cheapest_ticket, get_broadway_tickets, fetch_stubhub_data_with_dates, add_tracked_event, find_event_id
from todaytix import todaytix_fetch
import pytz

# Load the .env file if present (for local development)
load_dotenv()

app.secret_key = os.getenv('FLASK_SECRET_KEY')
google_client_id = os.getenv('GOOGLE_CLIENT_SECRET')

# Enable CORS
app.config['CORS_SUPPORTS_CREDENTIALS'] = True
app.config['CORS_HEADERS'] = ['Content-Type', 'Accept', 'Authorization', 'Origin']
app.config['CORS_RESOURCES'] = {r"/api/*": {"origins": [
    "http://localhost:5174", 
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "http://192.168.1.174:5173",
    "https://broadwaycommunity.vercel.app"
]}}

CORS(app)

# Configure Redis for sessions
# app.config["SESSION_TYPE"] = "redis"  # Use Redis as the session store
# app.config["SESSION_PERMANENT"] = True
# app.config["SESSION_USE_SIGNER"] = True  # Adds a layer of security to cookies
# app.config["SESSION_KEY_PREFIX"] = "flask-session:"  # Prefix for keys in Redis
# app.config["SESSION_REDIS"] = Redis(
#     host=os.getenv('REDIS_HOST'), 
#     port=int(os.getenv('REDIS_PORT')),  # Use environment variable or default port 6379
#     password=os.getenv('REDIS_PASSWORD'),  # Make sure to set this in your environment
#     ssl=True
# )
# app.config["SESSION_COOKIE_SAMESITE"] = "None"
# # app.config['SESSION_COOKIE_HTTPONLY'] = True
# # app.config["SESSION_COOKIE_SECURE"] = True
# app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# Initialize Flask-Session
# Session(app)

bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

from models import User, Event, Event_Alert, Category_Alert, Event_Info, Category, Token, Venue

############# Routes #############
@app.route("/")
def root():
    return "<h1>Welcome to the simple json server<h1>"

@app.get('/api/check_session')
def check_session():
    user = db.session.get(User, session.get('user_id'))
    if user:
        print(f'{user.first_name} {user.last_name} is signed in')
        print(f'check session {session.get("user_id")}')
        return user.to_dict(rules=['-password_hash']), 200
    else:
        return {"message": "No user logged in"}, 401

@app.post('/api/login')
def login():
    print('login')
    data = request.json
    user = User.query.filter(User.email == data.get('email')).first()
    if user and bcrypt.check_password_hash(user.password_hash, data.get('password')):
        session.permanent = True
        session["user_id"] = user.id
        print(f'{user.first_name} {user.last_name} logged in')
        return user.to_dict(), 200
    else:
        return { "error": "Invalid username or password" }, 401

@app.delete('/api/logout')
def logout():
    try:
        session.clear()
        response = jsonify({"message": "Logged out successfully"})
        response.set_cookie('session', '', expires=0)  # Clear session cookie
        return response, 200
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return jsonify({"error": "Logout failed"}), 500
    
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

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    data = request.json
    user_info = data.get('userInfo')
    
    try:
        if user_info:
            email = user_info.get('email')
            name = user_info.get('name')
            
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Create new user
                # You might want to split the name into first_name and last_name
                names = name.split(' ', 1)
                first_name = names[0]
                last_name = names[1] if len(names) > 1 else ''
                
                user = User(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    # Set other fields as needed
                )
                db.session.add(user)
                db.session.commit()
            
            # Set session
            session.permanent = True
            session["user_id"] = user.id
            
            return jsonify({
                'success': True,
                'user': user.to_dict()
            })
            
        return jsonify({'error': 'Invalid user info'}), 400
        
    except Exception as e:
        print(f"Error in google_auth: {str(e)}")
        return jsonify({'error': 'Authentication failed'}), 400
    
@app.route('/api/events', methods=['GET', 'POST'])
def get_events():
    if request.method == 'GET':
        events = []
        for event in Event.query.all():
            event_dict = event.to_dict()
            event_dict.pop('event_alerts', None)
            event_dict['category'].pop('category_alerts', None)
            events.append(event_dict)

        response = make_response(events,200)
        return response

    elif request.method == 'POST':
        try:
            data = request.get_json()
            print("Received data:", data)  # Debug print
            
            # First, handle venue if it exists
            venue_id = data.get('venue_id')  # Get venue_id from the request data
            
            created_events = []
            # Create an event for each selected Stubhub category
            stubhub_category = data.get('stubhub_categories')
            if not stubhub_category:
                return jsonify({"error": "Stubhub category is required"}), 400

            new_event = Event(
                name=data['name'],
                stubhub_category_id=str(stubhub_category),  # Make sure it's a string
                category_id=data['category_id'],
                venue_id=venue_id  # Include the venue_id here
            )
            db.session.add(new_event)
            created_events.append(new_event)
            
            db.session.commit()

            fetch_stubhub_data([new_event])
            
            # Return all created events
            return jsonify([event.to_dict() for event in created_events]), 201

        except Exception as e:
            print("Error:", str(e))  # Debug print
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

@app.route('/api/event_names', methods=['GET', 'POST'])
def get_event_names():
    if request.method == 'GET':
        events = []
        for event in Event.query.all():
            event_name = event.name
            events.append(event_name)

        response = make_response(events,200)

        return response

@app.route('/api/events/<int:id>', methods=['GET','POST'])
def get_event(id):
    if request.method == 'GET':
        event_id = db.session.get(Event, id)
        if not event_id:
            return {"error": f"event with id {id} not found"}, 404
        return event_id.to_dict()

@app.route('/api/events/name/<string:name>', methods=['GET'])
def get_event_by_name(name):
    if request.method == 'GET':
        event_entry = Event.query.filter_by(name=name).first()
        if not event_entry:
            return {"error": f"Event with name '{name}' not found"}, 404
        return event_entry.to_dict()

@app.route('/api/event_alerts', methods=['GET', 'POST'])
def get_event_alerts():
    if request.method == 'GET':
        event_alerts = []
        for alert in Event_Alert.query.all():
            alert_dict = alert.to_dict()
            event_alerts.append(alert_dict)

        response = make_response(event_alerts,200)

        return response

    elif request.method == 'POST':
        event_name=request.json.get("event_name")
        
        event = Event.query.filter(Event.name == event_name).first()
        

        new_alert = Event_Alert(
            user_id=request.json.get("user_id"),
            event_id=request.json.get("event_id"),
            price_number=request.json.get("price_number"),
            price_percent=request.json.get("price_percent"),
            start_date=request.json.get("start_date"),
            end_date=request.json.get("end_date"),
            show_time=request.json.get("show_time"),
            notification_method=request.json.get("notification_method"),
            weekday=request.json.get("weekday")
        )
        print(new_alert.to_dict())

        db.session.add(new_alert)
        db.session.commit()
        
        new_alert_dict = new_alert.to_dict()

        response = make_response(new_alert_dict, 201)

        return response

@app.route('/api/event_alerts/<int:id>', methods=['PATCH', 'DELETE'])
def edit_event_alerts(id):
    alert = db.session.get(Event_Alert, id)
    if not alert:
        return {"error": f"Event Alert with id {id} not found"}, 404
    
    if request.method == 'DELETE':    
        db.session.delete(alert)
        db.session.commit()
        return {}, 202

    elif request.method == 'PATCH':
        try:
            data = request.json
            
            # Update all the new fields
            if 'price_number' in data:
                alert.price_number = data['price_number']
            if 'price_percent' in data:
                alert.price_percent = data['price_percent']
            if 'start_date' in data:
                alert.start_date = data['start_date']
            if 'end_date' in data:
                alert.end_date = data['end_date']
            if 'show_time' in data:
                alert.show_time = data['show_time']
            if 'notification_method' in data:
                alert.notification_method = data['notification_method']
            if 'weekday' in data:
                alert.weekday = data['weekday']
            
            db.session.add(alert)
            db.session.commit()
            return alert.to_dict(), 200
        except Exception as e:
            return {"error": f'{e}'}

@app.route('/api/category_alerts', methods=['GET', 'POST'])
def get_category_alerts():
    if request.method == 'GET':
        category_alerts = []
        for alert in Category_Alert.query.all():
            alert_dict = alert.to_dict()
            category_alerts.append(alert_dict)

        response = make_response(category_alerts,200)

        return response
    
    elif request.method == 'POST':
        category_name=request.json.get("category_name")

        category = Category.query.filter(Category.name == category_name).first()

        new_alert = Category_Alert(
            user_id=request.json.get("user_id"),
            category_id=request.json.get("category_id"),
            price_number=request.json.get("price_number"),
            price_percent=request.json.get("price_percent"),
            start_date=request.json.get("start_date"),
            end_date=request.json.get("end_date"),
            show_time=request.json.get("show_time"),
            notification_method=request.json.get("notification_method"),
            weekday=request.json.get("weekday")
        )

        db.session.add(new_alert)
        db.session.commit()
        
        new_alert_dict = new_alert.to_dict()

        response = make_response(new_alert_dict, 201)

        return response

@app.route('/api/category_alerts/<int:id>', methods=['PATCH', 'DELETE'])
def edit_category_alerts(id):
    alert = db.session.get(Category_Alert, id)
    if not alert:
        return {"error": f"Category Alert with id {id} not found"}, 404

    if request.method == 'DELETE':
        db.session.delete(alert)
        db.session.commit()
        return {}, 202

    elif request.method == 'PATCH':
        try:
            data = request.json
            
            # Update all the new fields
            if 'price_number' in data:
                alert.price_number = data['price_number']
            if 'price_percent' in data:
                alert.price_percent = data['price_percent']
            if 'start_date' in data:
                alert.start_date = data['start_date']
            if 'end_date' in data:
                alert.end_date = data['end_date']
            if 'show_time' in data:
                alert.show_time = data['show_time']
            if 'notification_method' in data:
                alert.notification_method = data['notification_method']
            if 'weekday' in data:
                alert.weekday = data['weekday']
            
            db.session.add(alert)
            db.session.commit()
            return alert.to_dict(), 200
        except Exception as e:
            return {"error": f'{e}'}

@app.route('/api/categories', methods=['GET', 'POST'])
def get_categories():
    if request.method == 'GET':
        categories = []
        for category in Category.query.order_by(Category.id.desc()).all():
            category_dict = category.to_dict()
            categories.append(category_dict)

        response = make_response(categories,200)

        return response
    
@app.route('/api/category_names', methods=['GET'])
def get_category_names():
    if request.method == 'GET':
        categories = []
        for category in Category.query.all():
            categories.append({
                "id": category.id,
                "name": category.name
            })
        return make_response(jsonify(categories), 200)
    
@app.route('/api/categories/<string:name>', methods=['GET', 'POST'])
def get_category_by_name(name):
    category = db.session.query(Category).filter_by(name=name).first()
    category_dict = category.to_dict()
    category_dict.pop('category_alerts', None)
    
    if 'event' in category_dict and isinstance(category_dict['event'], list):
        for event in category_dict['event']:
            event.pop('event_alerts', None)  # Remove 'event_alerts' from each event dict

    return category_dict

@app.route('/api/fetch_tickets', methods=['POST'])
def refresh_stubhub_data():
    try:
        events = db.session.query(Event).all()
        fetch_stubhub_data(events)
        return {"message": "StubHub data fetched successfully"}, 200
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/fetch_tickets/<string:category>', methods=['POST'])
def refresh_ticket_data_category(category):
    try:
        events = db.session.query(Event).join(Category).filter(Category.name == category).all()

        if not events:
            return {"error": "No events found for the given category"}, 404
        data = fetch_stubhub_data(events)
        response = make_response(data,200)
        return response
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/fetch_ticket/<int:id>', methods=['POST'])
def refresh_individual_ticket_data(id):
    print(f"fetching ticket data")
    try:
        event = db.session.query(Event).filter(Event.id == id).first()
        
        data = fetch_stubhub_data([event])
        
        response = make_response(data,200)
        return response
    except Exception as e:
        return {"error": str(e)}, 500
    
@app.route('/api/fetch_tickets_dates/<string:category>', methods=['POST'])
def refresh_ticket_data_by_dates(category):
    try:
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        events = db.session.query(Event).join(Category).filter(Category.name == category).all()
        
        data = fetch_stubhub_data_with_dates(events, start_date, end_date)
        
        response = make_response(data,200)
        return response
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/fetch_todaytix/<int:id>', methods=['GET'])
def fetch_today_tix_data(id):
    try:
        event = db.session.query(Event).filter(Event.id == id).first()
        data = todaytix_fetch(event.todaytix_category_id)
        today_tix_price = data["data"]["fromPrice"]["value"]
        response = make_response({"today_tix_price": today_tix_price}, 200)
        return response
    except Exception as e:
        return {"error": str(e)}, 500
    
@app.route('/api/add_tracked_event', methods=['GET'])
def add_tracked_event_route():
    try:
        # Get the link from query parameters
        stubhub_link = request.args.get('link')
        
        if not stubhub_link:
            return jsonify({"error": "No Stubhub link provided"}), 400
            
        try:
            event_data = add_tracked_event(stubhub_link)  # Pass the user's link to the function
            return make_response(jsonify(event_data), 200)
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/venues', methods=['POST'])
def create_venue():
    try:
        data = request.get_json()
        
        # Check if venue already exists
        existing_venue = Venue.query.filter_by(
            stubhub_venue_id=str(data['stubhub_venue_id'])  # Convert to string
        ).first()
        
        if existing_venue:
            return jsonify(existing_venue.to_dict()), 200
            
        # Create new venue if it doesn't exist
        new_venue = Venue(
            name=data['name'],
            stubhub_venue_id=str(data['stubhub_venue_id']),  # Convert to string
            latitude=str(data['latitude']),                   # Convert to string
            longitude=str(data['longitude'])                  # Convert to string
        )
        
        db.session.add(new_venue)
        db.session.commit()
        
        return jsonify(new_venue.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/api/cron/fetch-all-tickets', methods=['POST'])
def cron_refresh_all_data():
    try:
        # Verify the request is from GitHub Actions
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != f"Bearer {os.getenv('CRON_SECRET_KEY')}":
            return {"error": "Unauthorized"}, 401

        # Get category from query parameter, default to first category if none provided
        category_name = request.args.get('category')
        
        if category_name:
            # Fetch events for specific category
            events = db.session.query(Event).join(Category).filter(
                Category.name == category_name,
                Event.closed != True  # Filter out closed events
            ).all()
        else:
            # If no category specified, get first category's events
            first_category = db.session.query(Category).first()
            if first_category:
                events = Event.query.filter(
                    Event.category_id == first_category.id,
                    Event.closed != True  # Filter out closed events
                ).all()
            else:
                events = []
            category_name = first_category.name if first_category else "none"

        # Get current time in EST
        est = pytz.timezone('US/Eastern')
        current_time = datetime.now(est)

        # Fetch and update data
        updated_data = fetch_stubhub_data(events)
        
        return {
            "message": "Cron job completed successfully",
            "category": category_name,
            "events_processed": len(events),
            "timestamp": current_time.isoformat(),
            "timezone": "EST"
        }, 200
        
    except Exception as e:
        print(f"Cron job error: {str(e)}")
        return {"error": str(e)}, 500

@app.route('/api/events/ids', methods=['GET'])
def get_event_ids():
    events = db.session.query(Event.id).filter(Event.closed != True).all()
    return jsonify([event[0] for event in events])

@app.route('/api/cron/fetch-event', methods=['POST'])
def cron_refresh_event():
    try:
        # Verify the request is from GitHub Actions
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != f"Bearer {os.getenv('CRON_SECRET_KEY')}":
            return {"error": "Unauthorized"}, 401

        # Get event ID from query parameter
        event_id = request.args.get('event_id')
        if not event_id:
            return {"error": "No event ID provided"}, 400
            
        # Fetch single event
        event = db.session.query(Event).get(event_id)
        if not event:
            return {"error": "Event not found"}, 404

        # Get current time in EST
        est = pytz.timezone('US/Eastern')
        current_time = datetime.now(est)

        # Fetch and update data for single event
        updated_data = fetch_stubhub_data([event])
        
        return {
            "message": "Event update completed successfully",
            "event_id": event_id,
            "event_name": event.name,
            "timestamp": current_time.isoformat(),
            "timezone": "EST"
        }, 200
        
    except Exception as e:
        print(f"Cron job error: {str(e)}")
        return {"error": str(e)}, 500

@app.route('/api/check_existing_events', methods=['GET'])
def check_existing_events():
    try:
        # Get comma-separated list of stubhub category IDs from query parameters
        stubhub_categories = request.args.get('stubhub_categories')
        if not stubhub_categories:
            return jsonify({"error": "No category IDs provided"}), 400

        # Split into list and remove any empty strings
        category_ids = [cat for cat in stubhub_categories.split(',') if cat]

        # Initialize result dictionary
        result = {}

        # Query events for each category ID
        for category_id in category_ids:
            events = Event.query.filter_by(stubhub_category_id=category_id).all()
            
            # Track which venue types exist for this category
            has_specific = any(event.venue_id is not None for event in events)
            has_any = any(event.venue_id is None for event in events)

            result[category_id] = {
                "specific": has_specific,
                "any": has_any
            }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)