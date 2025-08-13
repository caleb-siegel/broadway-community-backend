from db import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin
import string
from datetime import date, time
try:
    from sqlalchemy.dialects.postgresql import ARRAY
except ImportError:
    # Fallback for non-PostgreSQL databases
    ARRAY = None

class User (db.Model, SerializerMixin):
    __tablename__ = "user"
    
    serialize_rules = ["-event_alerts.user", "-category_alerts.user"]
    
    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String)
    phone_number = db.Column(db.String, nullable=True)
    sms_consent = db.Column(db.Boolean, default=False)

    event_alerts = db.relationship("Event_Alert", back_populates="user")
    category_alerts = db.relationship("Category_Alert", back_populates="user")

class Token (db.Model, SerializerMixin):
    __tablename__ = "token"

    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String)
    expires_at = db.Column(db.DateTime)

class Event_Alert (db.Model, SerializerMixin):
    __tablename__ = "event_alert"
    
    serialize_rules = ["-user.event_alerts", "-event.event_alerts"]
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    price_number = db.Column(db.Numeric(scale=2), nullable=True)
    price_percent = db.Column(db.Numeric(scale=2), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    show_time = db.Column(db.String, nullable=True)
    ticket_location = db.Column(db.String, nullable=True)
    ticket_row = db.Column(db.String, nullable=True)
    ticket_quantity = db.Column(db.String, nullable=True)
    ticket_note = db.Column(db.String, nullable=True)
    notification_method = db.Column(db.String, nullable=False)
    weekday = db.Column(ARRAY(db.Integer) if ARRAY else db.Text, nullable=True)
    created_on = db.Column(db.Date, default=date.today, nullable=True)
    
    user = db.relationship("User", back_populates="event_alerts")
    event = db.relationship("Event", back_populates="event_alerts")

class Category_Alert (db.Model, SerializerMixin):
    __tablename__ = "category_alert"
    
    serialize_rules = ["-user.event_alerts", "-user.category_alerts", "-category.category_alerts", "-category.event.event_alerts", "-category.event.category", "-category.event.category_id", "-category.event.image", "-category.event.lottery_url", "-category.event.name", "-category.event.show_duration"]
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    price_number = db.Column(db.Numeric(scale=2), nullable=True)   
    price_percent = db.Column(db.Numeric(scale=2), nullable=True)   
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    show_time = db.Column(db.String, nullable=True)
    ticket_location = db.Column(db.String, nullable=True)
    ticket_row = db.Column(db.String, nullable=True)
    ticket_quantity = db.Column(db.String, nullable=True)
    ticket_note = db.Column(db.String, nullable=True)
    notification_method = db.Column(db.String, nullable=False)
    weekday = db.Column(ARRAY(db.Integer) if ARRAY else db.Text, nullable=True)
    created_on = db.Column(db.Date, default=date.today, nullable=True)

    user = db.relationship("User", back_populates="category_alerts")
    category = db.relationship("Category", back_populates="category_alerts")

class Category (db.Model, SerializerMixin):
    __tablename__ = "category"

    serialize_rules = ["-category_alerts.category", "-event.category"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    category_alerts = db.relationship("Category_Alert", back_populates="category")
    event = db.relationship("Event", back_populates="category")

class Event (db.Model, SerializerMixin):
    __tablename__ = "event"

    serialize_rules = ["-event_alerts.event", "-event_info.event", "-category.event", "-venue.event"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    stubhub_category_id = db.Column(db.String)
    todaytix_category_id = db.Column(db.String)
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=True)
    lottery_url = db.Column(db.String, nullable=True)
    show_duration = db.Column(db.String, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    image = db.Column(db.String, nullable=True)
    closed = db.Column(db.Boolean, default=False)
    # description = db.Column(db.String, nullable=True)

    event_alerts = db.relationship("Event_Alert", back_populates="event")
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
    average_denominator = db.Column(db.Integer, nullable=True)
    average_lowest_price = db.Column(db.Numeric(scale=2), nullable=True)
    updated_at = db.Column(db.DateTime, default=date.today, nullable=True)
    location = db.Column(db.String, nullable=True)
    row = db.Column(db.String, nullable=True)
    quantity = db.Column(db.String, nullable=True)
    note = db.Column(db.String, nullable=True)

    event = db.relationship("Event", back_populates="event_info")

class Venue (db.Model, SerializerMixin):
    __tablename__ = "venue"

    serialize_rules = ["-event.venue", "-region.venue"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    stubhub_venue_id = db.Column(db.String)
    latitude = db.Column(db.String)
    longitude = db.Column(db.String)
    seatplan_url = db.Column(db.String, nullable=True)
    region_id = db.Column(db.Integer, db.ForeignKey("region.id"))

    event = db.relationship("Event", back_populates="venue")
    region = db.relationship("Region", back_populates="venue")

class Region (db.Model, SerializerMixin):
    __tablename__ = "region"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    venue = db.relationship("Venue", back_populates="region")
