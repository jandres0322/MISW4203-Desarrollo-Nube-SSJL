from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250))
    password = db.Column(db.String(500))
    email = db.Column(db.String(200))
    tasks = relationship('Task', backref='user', cascade="all, delete-orphan")
    created = db.Column(db.DateTime(timezone=True), default=datetime.now)                       
    updated = db.Column(db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time_stamp = db.Column(db.DateTime, default=func.now())
    path_file = db.Column(db.String(250))
    path_file_new_format = db.Column(db.String(250))
    new_format = db.Column(db.String(250))
    status = db.Column(Enum("Uploaded", "Processed", name="task_status_enum"), default="Uploaded")
    user_id = db.Column(db.Integer, ForeignKey('user.id'))
    created = db.Column(db.DateTime(timezone=True), default=datetime.now)                       
    updated = db.Column(db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

