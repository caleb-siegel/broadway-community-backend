from flask import Flask, make_response, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from models import db, User, Show, Show_Preference, Show_Info, Ticket_Info
from dotenv import dotenv_values
from flask_bcrypt import Bcrypt
import json
import random
from datetime import datetime

from api import partnerize_tracking_link, show_api_endpoints, show_api_endpoints2, get_link, get_stubhub_token, get_broadway_tickets, find_cheapest_ticket

config = dotenv_values(".env")

app = Flask(__name__)
app.secret_key = config['FLASK_SECRET_KEY']
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = config["SQLALCHEMY_DATABASE_URI"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

db.init_app(app)

@app.route("/")
def root():
    return "<h1>Welcome to the simple json server<h1>"

# @app.get('/api/check_session')
# def check_session():
#     user = db.session.get(User, session.get('user_id'))
#     print(f'check session {session.get("user_id")}')
#     if user:
#         return user.to_dict(rules=['-password_hash']), 200
#     else:
#         return {"message": "No user logged in"}, 401

# @app.delete('/api/logout')
# def logout():
#     session.pop('user_id')
#     return { "message": "Logged out"}, 200

# @app.post('/api/login')
# def login():
#     print('login')
#     data = request.json
#     user = User.query.filter(User.name == data.get('name')).first()
#     if user and bcrypt.check_password_hash(user.password_hash, data.get('password')):
#         session["user_id"] = user.id
#         print("success")
#         return user.to_dict(), 200
#     else:
#         return { "error": "Invalid username or password" }, 401
    
# @app.route('/api/user', methods=['GET', 'POST'])
# def user():
#     if request.method == 'GET':
#         users = [user.to_dict() for user in User.query.all()]
#         return make_response( users, 200 )
    
#     elif request.method == 'POST':
#         data = request.json
#         try:
#             new_user = User(
#                 name= data.get("name"),
#                 password_hash= bcrypt.generate_password_hash(data.get("password_hash"))
#             )
#             db.session.add(new_user)
#             db.session.commit()
            
#             return new_user.to_dict(), 201
#         except Exception as e:
#             print(e)
#             return {"error": f"could not post user: {e}"}, 405

@app.route('/api/shows', methods=['GET', 'POST'])
def shows():
    if request.method == 'GET':
        token = get_stubhub_token("4XWc10UmncVBoHo3lT8b", "sfwKjMe6h1cApxw1Ca7ZKTsaoa2gSRov5ECYkM2pVXEvAUW0Ux0KViQZwWfI")
        show_data = []
        i = 1
        for show in show_api_endpoints2:
            # call the stubhub api and return the cheapest ticket
            endpoint = get_link(show["category_id"], show["latitude"], show["longitude"])
            events_data = get_broadway_tickets(token, endpoint)
            print(events_data)
            if events_data["_embedded"]["items"]:
                cheapest_ticket = find_cheapest_ticket(events_data)
            
                # reformat date
                start_date = cheapest_ticket["start_date"]
                formatted_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S%z")
                formatted_date = formatted_date.strftime("%a, %b %-d, %Y %-I%p")
                formatted_date = formatted_date[:-2] + formatted_date[-2:].lower()

                # build show info object
                cheapest_ticket_object = {
                    "id": i,
                    "name": cheapest_ticket["name"],
                    "start_date": start_date,
                    "formatted_date": formatted_date,
                    "min_ticket_price": round(cheapest_ticket["min_ticket_price"]["amount"]),
                    "href": partnerize_tracking_link + cheapest_ticket["_links"]["event:webpage"]["href"],
                    "venue_name": cheapest_ticket["_embedded"]["venue"]["name"],
                }
                i += 1

            if cheapest_ticket_object:
                show_data.append(cheapest_ticket_object)

        
        # shows_data = [show.to_dict() for show in show_data]
        return make_response( show_data, 200 )
    


if __name__ == "__main__":
    app.run(debug=True)