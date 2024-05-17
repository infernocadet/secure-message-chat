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
def insert_user(username: str, password: str, role: int):
    with Session(engine) as session:
        user = User(username=username, password=password, role=role)
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)
    
def get_role(username: str):
    with Session(engine) as session:
        user = session.get(User, username)
        return user.role

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

# Adds user to existing room - wont be used. Wanted feature
# def add_user_to_room(username, room_id):
#     """
#     Can add user to an existing room. 
#     """
#     with Session(engine) as session:
#         user = session.query(User).filter_by(username=username).first()
#         room = session.query(Room).filter_by(id=room_id).first()
#         if user and room:
#             room.users.append(user)
#             session.commit()

def get_user_rooms(username):
    """
    Retrieves all rooms a user is part of.
    """
    with Session(engine) as session:
        user = session.query(User).filter_by(username=username).first()
        if user:
            return user.rooms
        return []
        
def find_room_with_users(usernames):
    """
    Tries to find an existing room with given usernames. 
    """
    with Session(engine) as session:
        # normalise names by sorting
        sorted_usernames = sorted(usernames)

        # query our rooms table to see if there is such a room
        rooms = session.query(Room).all()
        for room in rooms:
            # get all usernames in current room
            room_usernames = sorted([user.username for user in room.users])
            if room_usernames == sorted_usernames:
                return room
        
        # if no room found
        return None

def create_room(name: str, usernames: list) -> int:
    """
    Creates a new room and adds users to it.
    """
    with Session(engine) as session:

        existing_room = find_room_with_users(usernames)
        if existing_room:
            return existing_room.id

        # if no existing room found
        new_room = Room(name=name)
        session.add(new_room)
        session.commit()
        
        # add users to the room 
        for username in usernames:
            user = session.query(User).filter_by(username=username).first()
            if user:
                new_room.users.append(user)
        
        session.commit()
        return new_room.id