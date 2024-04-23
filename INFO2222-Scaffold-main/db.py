'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine, func
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


def create_room_in_db(room_id, sender, receiver):
    with Session(engine) as session:
        new_room = Rooms(id=room_id)
        session.add(new_room)

        # create participant entries
        session.add(RoomParticipants(room_id=room_id, user_username=sender))
        session.add(RoomParticipants(room_id=room_id, user_username=receiver))

        session.commit()


def find_room_with_users(user1, user2):
    with Session(engine) as session:
        # find rooms where user 1 is a participant
        query1 = session.query(RoomParticipants.room_id).filter_by(user_username=user1)
        # Find rooms where user2 is also a participant
        query2 = session.query(RoomParticipants.room_id).filter_by(user_username=user2)

        # find a room id present in both queries and no other participants
        room_id = session.query(query1.intersect(query2).subquery()).\
                  outerjoin(RoomParticipants, RoomParticipants.room_id == query1.c.room_id).\
                  group_by(RoomParticipants.room_id).\
                  having(func.count(RoomParticipants.room_id) == 2).scalar()
                  
        return room_id
    
#TODO:
# make sure that we dont create duplicate rooms
# store messages in the messages table
# when we join an existing room, if the room exists, check the messages table to load up messages