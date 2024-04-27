'''
db
database file, containing all the logic to interface with the sql database
'''

from flask import jsonify
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *
from pathlib import Path

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, password: str, public_key: str):
    with Session(engine) as session:
        user = User(username=username, password=password, public_key=public_key)
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)

# save chat message to database
def save_msg(sender: str, receiver: str, message: str):
    with Session(engine) as session:
        msg = Message(sender=sender, receiver=receiver, message=message['cipherText'], iv=json.dumps(
            message['iv']), hmac=message['hmac'])
        session.add(msg)
        session.commit()

# get history message from database
def get_history_msg(username):
    with Session(engine) as session:
        msg = session.query(Message).filter_by(
            sender=username, receiver=username).all()
        return msg
