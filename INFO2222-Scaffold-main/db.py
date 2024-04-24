'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine, func, Table, Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, Session, mapped_column
from typing import List
from pathlib import Path
from models import Room

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
class Base(DeclarativeBase):
    pass

# helper friends table, to link users together for a many-to-many relationship
# columns are composite keys to ensure not null and unique pairs
# user_id and friend_id are foreign keys which point to the main user.username
friend_table = Table('friends', Base.metadata,
                     Column('user_id', String, ForeignKey(
                         'user.username'), primary_key=True),
                     Column('friend_id', String, ForeignKey(
                         'user.username'), primary_key=True)
                     )


# model to store user information
class User(Base):
    __tablename__ = "user"

    # looks complicated but basically means
    # I want a username column of type string,
    # and I want this column to be my primary key
    # then accessing john.username -> will give me some data of type string
    # in other words we've mapped the username Python object property to an SQL column of type String
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    public_key: Mapped[str] = mapped_column(
        Text, nullable=True)  # Storing public key as text

    # establishing relationship with user model. joins with the friend_table.
    # back_populates ensures that adding friends is bi-directional
    friends: Mapped[List["User"]] = relationship(
        "User",
        secondary=friend_table,
        primaryjoin=username == friend_table.c.user_id,
        secondaryjoin=username == friend_table.c.friend_id,
        back_populates="friends"
    )

    sent_requests: Mapped[List["FriendRequest"]] = relationship(
        "FriendRequest",
        foreign_keys="[FriendRequest.sender_id]",
        backref="sender"
    )
    received_requests: Mapped[List["FriendRequest"]] = relationship(
        "FriendRequest",
        foreign_keys="[FriendRequest.receiver_id]",
        backref="receiver"
    )


class FriendRequest(Base):
    __tablename__ = "friendrequests"
    # in the case we want to track if a user is spamming requests
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_id: Mapped[str] = mapped_column(String, ForeignKey('user.username'))
    receiver_id: Mapped[str] = mapped_column(
        String, ForeignKey('user.username'))
    # ["rejected", "pending", "accepted"]
    status: Mapped[str] = mapped_column(String)

class Rooms(Base):
    __tablename__ = "rooms"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    active_participants: Mapped[List[str]] = mapped_column(Text)

    def create_room(self, sender: str, receiver: str):
        self.active_participants = [sender, receiver]
        self.dict = {sender: self.id, receiver: self.id}
        return self.id

    def is_active(self, user: str):
        return user in self.active_participants

    def get_room_id(self, user: str):
        if user not in self.dict:
            return None
        return self.dict[user]

    def add_participant(self, user: str):
        self.active_participants.append(user)
        self.dict[user] = self.id

    def remove_participant(self, user: str):
        self.active_participants.remove(user)
        del self.dict[user]

    def get_participants(self):
        return self.active_participants


class Message(Base):
    __tablename__ = "message"
    message_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    main_user: Mapped[str] = mapped_column(
        String, ForeignKey('user.username'), nullable=False)
    sender_id: Mapped[str] = mapped_column(
        String, ForeignKey('user.username'), nullable=False)
    encrypted_message: Mapped[str] = mapped_column(Text, nullable=False)

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

# Function to create a new room if it doesn't already exist


def create_room_in_db(session, sender: str, receiver: str) -> int:

    # Check if there is an existing room between sender and receiver
    existing_room = session.query(Room).filter(
        func.count(Room.active_participants) == 2,
        Room.active_participants.like(f"%{sender}%"),
        Room.active_participants.like(f"%{receiver}%"),
        Room.dict.has_all([sender, receiver])
    ).group_by(Room.id).having(func.count(Room.id) == 2).first()

    if existing_room:
        return existing_room.id
    else:
        # Create a new room
        new_room = Room()
        room_id = new_room.create_room(sender, receiver)

        session.add(new_room)
        session.commit()

        return room_id

# Function to find an existing room for users who have initialized a room with each other


def find_room_with_users(session, user1: str, user2: str) -> int:
    # Find rooms where both users are participants
    rooms = session.query(Room).all()
    for room in rooms:
        if room.is_active(user1) and room.is_active(user2):
            return room.get_room_id(user1)

    return None  # No existing room found
