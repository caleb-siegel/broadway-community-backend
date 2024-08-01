from flask import Flask, make_response, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from models import db, User, Show, Show_Preference, Show_Info, Ticket_Info
from dotenv import dotenv_values
from flask_bcrypt import Bcrypt
import json
import random

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
        shows = [show.to_dict() for show in Show.query.all()]
        return make_response( shows, 200 )
    
    elif request.method == 'POST':
        new_show = Show(
            name=request.json.get("name"),
        )

        db.session.add(new_show)
        db.session.commit()
        
        new_show_dict = new_show.to_dict()

        response = make_response(
            new_show_dict,
            201
        )

        return response

if __name__ == "__main__":
    app.run(debug=True)