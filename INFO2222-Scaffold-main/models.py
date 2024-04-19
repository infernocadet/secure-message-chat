'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String, Table, Column, Integer, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Dict, List

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
    
    # looks complicated but basically means
    # I want a username column of type string,
    # and I want this column to be my primary key
    # then accessing john.username -> will give me some data of type string
    # in other words we've mapped the username Python object property to an SQL column of type String 
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
        self.initiators: Dict[int, str] = {} # maps room id to initiators username

    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        self.initiators[room_id] = sender
        return room_id
    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id

    def leave_room(self, user):
        if user not in self.dict.keys():
            return
        del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]
    
    def get_initiator(self, room_id: int):
        return self.initiators.get(room_id, None)
    
