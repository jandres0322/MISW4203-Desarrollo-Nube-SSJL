from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250))
    password = db.Column(db.String(500))
    email = db.Column(db.String(200))
    tasks = relationship('Task', backref='user', cascade="all, delete-orphan")

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time_stamp = db.Column(db.DateTime, default=func.now())
    file_name = db.Column(db.String(250))
    new_format = db.Column(db.String(250))
    status = db.Column(Enum("Uploaded", "Processed", name="task_status_enum"), default="Uploaded")
    user_id = db.Column(db.Integer, ForeignKey('user.id'))

