'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String, Table, Column, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Dict, List
from sqlalchemy import DateTime
from datetime import datetime, timezone
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

# similar helper table for rooms and users supporting a many to many relationship
user_room_table = Table(
    'user_room', Base.metadata,
    Column('user_id', String, ForeignKey('user.username'), primary_key=True),
    Column('room_id', Integer, ForeignKey('room.id'), primary_key=True)
)


# model to store user information
class User(Base):
    __tablename__ = "user"
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    role: Mapped[int] = mapped_column(Integer) # [0, 1, 2, 3] = [student, academic, admin-staff, admin-user]
    todo_items = relationship("ToDoItem", back_populates="user")
    articles = relationship('Article', back_populates='author', cascade="all, delete-orphan")
    comments = relationship('Comment', back_populates='author', cascade="all, delete-orphan")
    
    # deprecated - no more keys
    # public_key: Mapped[str] = mapped_column(Text, nullable=True) # Storing public key as text

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

    rooms: Mapped[List["Room"]] = relationship(
        "Room",
        secondary=user_room_table,
        back_populates="users"
    )

class FriendRequest(Base):
    __tablename__ = "friendrequests"
    # in the case we want to track if a user is spamming requests
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_id: Mapped[str] = mapped_column(String, ForeignKey('user.username'))
    receiver_id: Mapped[str] = mapped_column(String, ForeignKey('user.username'))
    status: Mapped[str] = mapped_column(String) # ["rejected", "pending", "accepted"]   

class Room(Base):
    __tablename__ = 'room'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_room_table,
        back_populates="rooms"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="room",
        cascade="all, delete-orphan"
    )

class Message(Base):
    __tablename__ = 'message'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    sender_username: Mapped[str]  = mapped_column(String, ForeignKey('user.username'))
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey('room.id'))

    sender: Mapped["User"] = relationship("User")
    room: Mapped["Room"] = relationship("Room", back_populates="messages")

class ToDoItem(Base):
    __tablename__ = 'todo_items'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.username'), nullable=False)
    description = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    user = relationship("User", back_populates="todo_items")

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(String, ForeignKey('user.username'))  # Correct table name
    author = relationship('User', back_populates='articles')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    comments = relationship('Comment', back_populates='article', cascade="all, delete-orphan")

# Comment model
class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    article_id = Column(Integer, ForeignKey('articles.id'))  
    author_id = Column(String, ForeignKey('user.username')) 
    article = relationship('Article', back_populates='comments')
    author = relationship('User', back_populates='comments')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
