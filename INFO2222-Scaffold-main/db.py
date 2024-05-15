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

def get_friends(username: str):
    with Session(engine) as session:
        user = session.get(User, username)
        return user.friends

def remove_friend(current_username: str, friend_username: str):
    with Session(engine) as session:
        current_user = session.query(User).filter_by(username=current_username).first()
        friend_user = session.query(User).filter_by(username=friend_username).first()

        if not current_user or not friend_user:
            return False, "User not found"

        # Remove friend relationship
        if friend_user in current_user.friends:
            current_user.friends.remove(friend_user)
            friend_user.friends.remove(current_user)
            session.commit()
            return True, None
        else:
            return False, "Friend relationship not found"