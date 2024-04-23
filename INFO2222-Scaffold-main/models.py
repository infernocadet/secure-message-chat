'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String, Table, Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Dict, List
from datetime import datetime, timezone
from db import create_room_in_db, find_room_with_users

# for friends database, using Table, Column, Integer, ForeignKey & relationship

# data models
class Base(DeclarativeBase):
    pass

# helper friends table, to link users together for a many-to-many relationship
# columns are composite keys to ensure not null and unique pairs
# user_id and friend_id are foreign keys which point to the main user.username
friend_table = Table('friends', Base.metadata, 
    Column('user_id', String, ForeignKey('user.username'), primary_key=True),
    Column('friend_id', String, ForeignKey('user.username'), primary_key=True)
)


# model to store user information
class User(Base):
    __tablename__ = "user"
    
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    public_key: Mapped[str] = mapped_column(Text, nullable=True) # Storing public key as text

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
    receiver_id: Mapped[str] = mapped_column(String, ForeignKey('user.username'))
    status: Mapped[str] = mapped_column(String) # ["rejected", "pending", "accepted"]   


class Rooms(Base):
    __tablename__ = "rooms"

    # room id as primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # list of participants in the room 
    participants: Mapped[List["User"]] = relationship('User', secondary='room_participants')

    # relationship with messages table
    messages: Mapped[List["Messages"]] = relationship("Messages", back_populates="room")


class RoomParticipants(Base):
    __tablename__ = "room_participants"
    
    room_id = Mapped[int] = mapped_column(Integer, ForeignKey('rooms.id'), primary_key=True)
    user_username = Mapped[str] = mapped_column(String, ForeignKey('user.username'), primary_key=True)


class Messages(Base):
    __tablename__ = "messages"

    # message id as primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # room id to reference chat room
    room_id = Mapped[int] = mapped_column(Integer, ForeignKey('rooms.id'), nullable=False)

    # the main user who is accessing the database, encrypting and decrypting the message
    main_user = Mapped[str] = mapped_column(String, ForeignKey('user.username'), nullable=False)

    # senders username to reference the sender of the message
    sender_id: Mapped[str] = mapped_column(String, ForeignKey('user.username'), nullable=False)

    # encrypted message content for both users
    encrypted_message_content: Mapped[str] = mapped_column(Text, nullable=False)

    # relationship with rooms table
    room: Mapped[Rooms] = relationship("Rooms", back_populates="messages")
    main_user_ref: Mapped[User] = relationship("User", foreign_keys=[main_user])
    sender_ref: Mapped[User] = relationship("User", foreign_keys=[sender_id])


# stateful counter used to generate the room id
class Counter():
    def __init__(self):
        self.counter = 0 
    
    def get(self):
        self.counter += 1
        return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        self.dict: Dict[str, int] = {}
        self.active_participants: Dict[int, set] = {}

    def create_room(self, sender: str, receiver: str) -> int:

        # check if there is an existing room with the two users
        existing_room_id = find_room_with_users(sender, receiver)
        if existing_room_id:
            self.dict[sender] = existing_room_id
            self.dict[receiver] = existing_room_id
            return existing_room_id

        # otherwise make a new room
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        self.active_participants[room_id] = set()

        # handle database insertion
        create_room_in_db(room_id, sender, receiver)

        return room_id

    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id
        self.active_participants[room_id].add(sender)

    def leave_room(self, user):
        if user in self.dict:
            room_id = self.dict[user]
            if user in self.active_participants[room_id]:
                self.active_participants[room_id].remove(user)
            if not self.active_participants[room_id]:  # If no active participants, cleanup
                del self.active_participants[room_id]
            del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]
    
    def is_active(self, user: str):
        room_id = self.get_room_id(user)
        return room_id in self.active_participants and user in self.active_participants[room_id]
    