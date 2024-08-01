from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin
import string
from datetime import date, time


metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)
db = SQLAlchemy(metadata=metadata)

class User(db.Model, SerializerMixin):
    __tablename__ = "user"
    
    serialize_rules = ["-show_preferences.user"]
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password_hash = db.Column(db.String)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)

    show_preferences = db.relationship("Show_Preferences", back_populates="user")

class Show_Preference(db.Model, SerializerMixin):
    __tablename__ = "show_preference"
    
    serialize_rules = ["-user.show_preferences", "-show.show_preferences"]
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    show_id = db.Column(db.Integer, db.ForeignKey("show.id"))
    price = db.Column(db.Numeric(scale=2), nullable=True)
    seat_region = db.Column(db.String, nullable=True)
    start_date = db.Column(db.Date, default=date.today, nullable=True)
    end_date = db.Column(db.Date, default=date.today, nullable=True)
    show_time = db.Column(db.Time, default=time(0, 0), nullable=True)

    user = db.relationship("User", back_populates="show_preferences")
    show = db.relationship("Show", back_populates="show_preferences")

class Show (db.Model, SerializerMixin):
    __tablename__ = "show"

    serialize_rules = ["-show_preferences.show", "-show_info.show", "-ticket_info.show"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    show_preferences = db.relationship("Show_Preferences", back_populates="show")
    show_info = db.relationship("Show_Info", back_populates="show")
    ticket_info = db.relationship("Ticket_Info", back_populates="show")

class Show_Info (db.Model, SerializerMixin):
    __tablename__ = "show_info"

    serialize_rules = ["-show.show_info"]

    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey("show.id"))
    theater = db.Column(db.String)
    lottery_url = db.Column(db.String, nullable=True)
    show_duration = db.Column(db.String)

    show = db.relationship("Show", back_populates="show_info")

class Ticket_Info (db.Model, SerializerMixin):
    __tablename__ = "ticket_info"

    serialize_rules = ["-show.ticket_info"]

    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey("show.id"))
    price = db.Column(db.Numeric(scale=2))
    seat_region = db.Column(db.String, nullable=True)
    seat_numbers = db.Column(db.String, nullable=True)
    number_of_seats = db.Column(db.Integer, nullable=True)
    show_time = db.Column(db.Time, default=time(0, 0), nullable=True)
    show_date = db.Column(db.Date, default=date.today, nullable=True)

    show = db.relationship("Show", back_populates="ticket_info")