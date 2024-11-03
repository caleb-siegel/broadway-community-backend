from db import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin
import string
from datetime import date, time

class User (db.Model, SerializerMixin):
    __tablename__ = "user"
    
    serialize_rules = ["-event_preferences.user", "-category_preferences.user"]
    
    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String)
    phone_number = db.Column(db.String, nullable=True)

    event_preferences = db.relationship("Event_Preference", back_populates="user")
    category_preferences = db.relationship("Category_Preference", back_populates="user")

class Token (db.Model, SerializerMixin):
    __tablename__ = "token"

    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String)
    expires_at = db.Column(db.DateTime)

class Event_Preference (db.Model, SerializerMixin):
    __tablename__ = "event_preference"
    
    serialize_rules = ["-user.event_preferences", "-event.event_preferences"]
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    price = db.Column(db.Numeric(scale=2), nullable=True)
    start_date = db.Column(db.Date, default=date.today, nullable=True)
    end_date = db.Column(db.Date, default=date.today, nullable=True)
    show_time = db.Column(db.Time, default=time(0, 0), nullable=True)

    user = db.relationship("User", back_populates="event_preferences")
    event = db.relationship("Event", back_populates="event_preferences")

class Category_Preference (db.Model, SerializerMixin):
    __tablename__ = "category_preference"
    
    serialize_rules = ["-user.category_preferences", "-category.category_preferences"]
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    price = db.Column(db.Numeric(scale=2), nullable=True)   
    start_date = db.Column(db.Date, default=date.today, nullable=True)
    end_date = db.Column(db.Date, default=date.today, nullable=True)
    show_time = db.Column(db.Time, default=time(0, 0), nullable=True)

    user = db.relationship("User", back_populates="category_preferences")
    category = db.relationship("Category", back_populates="category_preferences")

class Category (db.Model, SerializerMixin):
    __tablename__ = "category"

    serialize_rules = ["-category_preferences.category", "-event.category"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    category_preferences = db.relationship("Category_Preference", back_populates="category")
    event = db.relationship("Event", back_populates="category")

class Event (db.Model, SerializerMixin):
    __tablename__ = "event"

    serialize_rules = ["-event_preferences.event", "-event_info.event", "-category.event", "-venue.event"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    stubhub_category_id = db.Column(db.String)
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=True)
    lottery_url = db.Column(db.String, nullable=True)
    show_duration = db.Column(db.String, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    image = db.Column(db.String, nullable=True)

    event_preferences = db.relationship("Event_Preference", back_populates="event")
    event_info = db.relationship("Event_Info", back_populates="event")
    category = db.relationship("Category", back_populates="event")
    venue = db.relationship("Venue", back_populates="event")

class Event_Info (db.Model, SerializerMixin):
    __tablename__ = "event_info"

    serialize_rules = ["-event.event_info"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    price = db.Column(db.Numeric(scale=2))
    event_time = db.Column(db.Time, nullable=True)
    event_date = db.Column(db.Date, nullable=True)
    event_weekday = db.Column(db.Integer, nullable=True)
    formatted_date = db.Column(db.String, nullable=True)
    sortable_date = db.Column(db.DateTime, nullable=True)
    link = db.Column(db.String)
    updated_at = db.Column(db.DateTime, default=date.today, nullable=True)

    event = db.relationship("Event", back_populates="event_info")

class Venue (db.Model, SerializerMixin):
    __tablename__ = "venue"

    serialize_rules = ["-event.venue"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    stubhub_venue_id = db.Column(db.String)
    latitude = db.Column(db.String)
    longitude = db.Column(db.String)
    seatplan_url = db.Column(db.String, nullable=True)

    event = db.relationship("Event", back_populates="venue")
