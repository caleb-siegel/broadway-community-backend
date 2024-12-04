from flask import Flask, make_response, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS, cross_origin
from flask_session import Session
from dotenv import dotenv_values, load_dotenv
from flask_bcrypt import Bcrypt
from flask_session import Session
from redis import Redis
import json
from datetime import datetime, timedelta
import os
from db import db, app
from stubhub import get_stubhub_token, fetch_stubhub_data, get_category_link, find_cheapest_ticket, get_broadway_tickets, fetch_stubhub_data_with_dates
from todaytix import todaytix_fetch

# Load the .env file if present (for local development)
load_dotenv()

app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Enable CORS
CORS(app, 
    supports_credentials=True, 
    resources={r"/api/*": {
        "origins": ["http://localhost:5173", "https://broadwaycommunity.vercel.app"],
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "Authorization", "Origin"],
        "supports_credentials": True,
    }},
)

# Configure Redis for sessions
app.config["SESSION_TYPE"] = "redis"  # Use Redis as the session store
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_USE_SIGNER"] = True  # Adds a layer of security to cookies
app.config["SESSION_KEY_PREFIX"] = "flask-session:"  # Prefix for keys in Redis
app.config["SESSION_REDIS"] = Redis(
    host=os.getenv('REDIS_HOST'), 
    port=int(os.getenv('REDIS_PORT')),  # Use environment variable or default port 6379
    password=os.getenv('REDIS_PASSWORD'),  # Make sure to set this in your environment
    ssl=True
)
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config["SESSION_COOKIE_SECURE"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# Initialize Flask-Session
Session(app)

bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

from models import User, Event, Event_Preference, Category_Preference, Event_Info, Category, Token, Venue

############# Routes #############
@app.route("/")
def root():
    return "<h1>Welcome to the simple json server<h1>"

@app.get('/api/check_session')
def check_session():
    user = db.session.get(User, session.get('user_id'))
    print(user.name)
    print(f'check session {session.get("user_id")}')
    if user:
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
        print(f'sessions user_id: {session["user_id"]}')
        print("success")
        print(session)
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
    
@app.route('/api/events', methods=['GET', 'POST'])
def get_events():
    if request.method == 'GET':
        events = []
        for event in Event.query.all():
            event_dict = event.to_dict()
            events.append(event_dict)

        response = make_response(events,200)

        return response

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

@app.route('/api/event_preferences', methods=['GET', 'POST'])
def get_event_preferences():
    if request.method == 'GET':
        event_preferences = []
        for preference in Event_Preference.query.all():
            preference_dict = preference.to_dict()
            event_preferences.append(preference_dict)

        response = make_response(event_preferences,200)

        return response

    elif request.method == 'POST':
        event_name=request.json.get("event_name")

        event = Event.query.filter(Event.name == event_name).first()


        new_preference = Event_Preference(
            user_id=request.json.get("user_id"),
            event_id=event.id,
            price=request.json.get("price"),
            # start_date=request.json.get("start_date"),
            # end_date=request.json.get("end_date"),
            # show_time=request.json.get("show_time"),
            send_email=request.json.get("send_email"),
            send_sms=request.json.get("send_sms"),
            send_push=request.json.get("send_push"),
        )

        db.session.add(new_preference)
        db.session.commit()
        
        new_preference_dict = new_preference.to_dict()

        response = make_response(new_preference_dict, 201)

        return response

@app.route('/api/event_preferences/<int:id>', methods=['PATCH', 'DELETE'])
def edit_event_preferences(id):
    preference = db.session.get(Event_Preference, id)
    if not preference:
        return {"error": f"Event Preference with id {id} not found"}, 404
    
    if request.method == 'DELETE':    
        db.session.delete(preference)
        db.session.commit()
        return {}, 202

    elif request.method == 'PATCH':
        try:
            data = request.json
            setattr(preference, 'price', data['price'])
            db.session.add(preference)
            db.session.commit()
            return preference.to_dict(), 200
        except Exception as e:
            return {"error": f'{e}'}

@app.route('/api/category_preferences', methods=['GET', 'POST'])
def get_category_preferences():
    if request.method == 'GET':
        category_preferences = []
        for preference in Category_Preference.query.all():
            preference_dict = preference.to_dict()
            category_preferences.append(preference_dict)

        response = make_response(category_preferences,200)

        return response
    
    elif request.method == 'POST':
        category_name=request.json.get("category_name")

        category = Category.query.filter(Category.name == category_name).first()

        new_preference = Category_Preference(
            user_id=request.json.get("user_id"),
            category_id=category.id,
            price=request.json.get("price"),
            # start_date=request.json.get("start_date"),
            # end_date=request.json.get("end_date"),
            # show_time=request.json.get("show_time"),
            send_email=request.json.get("send_email"),
            send_sms=request.json.get("send_sms"),
            send_push=request.json.get("send_push"),
        )

        db.session.add(new_preference)
        db.session.commit()
        
        new_preference_dict = new_preference.to_dict()

        response = make_response(new_preference_dict, 201)

        return response

@app.route('/api/category_preferences/<int:id>', methods=['PATCH', 'DELETE'])
def edit_category_preferences(id):
    preference = db.session.get(Category_Preference, id)
    if not preference:
        return {"error": f"Category Preference with id {id} not found"}, 404

    if request.method == 'DELETE':
        db.session.delete(preference)
        db.session.commit()
        return {}, 202

    elif request.method == 'PATCH':
        try:
            data = request.json
            setattr(preference, 'price', data['price'])
            db.session.add(preference)
            db.session.commit()
            return preference.to_dict(), 200
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
    
@app.route('/api/category_names', methods=['GET', 'POST'])
def get_category_names():
    if request.method == 'GET':
        categories = []
        for category in Category.query.all():
            category_name = category.name
            categories.append(category_name)

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


if __name__ == "__main__":
    app.run(debug=True)