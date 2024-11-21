from flask import Flask, make_response, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import dotenv_values, load_dotenv
from flask_bcrypt import Bcrypt
import json
from datetime import datetime, timedelta
import os
from db import db, app
from stubhub import get_stubhub_token, fetch_stubhub_data, get_category_link, find_cheapest_ticket, get_broadway_tickets
from todaytix import todaytix_fetch

# Load the .env file if present (for local development)
load_dotenv()

app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Configure session settings
# app.config['SESSION_COOKIE_SECURE'] = True  # For HTTPS
# app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Required for cross-origin requests
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session duration

CORS(app, supports_credentials=True, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "https://broadwaycommunity.vercel.app"],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "Authorization"],
        "supports_credentials": True
    }
})

bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

from models import User, Event, Event_Preference, Category_Preference, Event_Info, Category, Token, Venue

############# Routes #############
@app.route("/")
def root():
    return "<h1>Welcome to the simple json server<h1>"

@app.get('/api/check_session')
def check_session():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"message": "No user logged in"}), 401
        
        user = User.query.get(user_id)
        if not user:
            session.pop('user_id', None)
            return jsonify({"message": "User not found"}), 401
            
        return jsonify(user.to_dict(rules=['-password_hash'])), 200
    except Exception as e:
        print(f"Session check error: {str(e)}")
        return jsonify({"message": "Session check failed"}), 500

@app.post('/api/login')
def login():
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Missing email or password"}), 400

        user = User.query.filter(User.email == data['email']).first()
        if user and bcrypt.check_password_hash(user.password_hash, data['password']):
            session.permanent = True  # Make the session permanent
            session['user_id'] = user.id
            print(f'session is {session} and session[user_id] is {session['user_id']}')
            return jsonify(user.to_dict(rules=['-password_hash'])), 200
        
        return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500

@app.delete('/api/logout')
def logout():
    try:
        session.clear()
        return jsonify({"message": "Logged out successfully"}), 200
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

@app.route('/api/category_preferences', methods=['GET', 'POST'])
def get_category_preferences():
    if request.method == 'GET':
        category_preferences = []
        for preference in Category_Preference.query.all():
            preference_dict = preference.to_dict()
            category_preferences.append(preference_dict)

        response = make_response(category_preferences,200)

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

@app.route('/api/fetch_tickets/<string:category>', methods=['POST'])
def refresh_ticket_data_category(category):
    try:
        events = db.session.query(Event).join(Category).filter(Category.name == category).all()
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

@app.route('/api/fetch_todaytix/<int:id>', methods=['GET'])
def fetch_today_tix_data(id):
    try:
        event = db.session.query(Event).filter(Event.id == id).first()
        data = todaytix_fetch(event.todaytix_category_id)
        print(data)
        today_tix_price = data["data"]["fromPrice"]["value"]
        response = make_response({"today_tix_price": today_tix_price}, 200)
        return response
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(debug=True)