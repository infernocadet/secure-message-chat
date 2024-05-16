'''
socket_routes
file containing all the routes related to socket.io
'''


from flask_socketio import join_room, emit, leave_room
from flask import request, jsonify
from bleach import clean 
import os
import base64

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

from models import Room

import db

from shared_state import user_sessions

room = Room()

# when the client connects to a socket
# this event is emitted when the io() function is called in JS
@socketio.on('connect')
def connect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")

    # mapping user to session id
    if username:
        user_sessions[username] = request.sid
        print(f"{username} connected with SID {user_sessions.get(username)}")

    if room_id is None or username is None:
        return
    # socket automatically leaves a room on client disconnect
    # so on client connect, the room needs to be rejoined
    print(f"Joining room {room_id} for {username}")
    join_room(int(room_id))
    emit("incoming", (f"{username} has connected", "green"), to=int(room_id))

# event when client disconnects
# quite unreliable use sparingly
@socketio.on('disconnect')
def disconnect():
    username = request.cookies.get("username")
    print(f"{username} disconnected")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
      
    if username in user_sessions:
        del user_sessions[username]
        # emit to friends that user is offline
        active_user_friends = db.get_friends(username)
        for friend in active_user_friends:
            if friend.username in user_sessions:
                emit("friend_offline", {"username": username}, room=user_sessions[friend.username])

    emit("incoming", (f"{username} has disconnected", "red"), to=int(room_id))
    leave_room(int(room_id))

# send message event handler
@socketio.on("send")
def send(username, message, room_id):
    print(message)
    emit("incoming", (f"{username}: {message}"), to=room_id)

@socketio.on("join")
def join(sender_name, receiver_name):
    
    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    room_id = room.get_room_id(receiver_name)

    # if the user is already inside of a room 
    if room_id is not None:
        
        room.join_room(sender_name, room_id)
        join_room(room_id)
        # emit to everyone in the room except the sender
        emit("incoming", (f"{sender_name} has joined the room.", "green"), to=room_id, include_self=False)
        # emit only to the sender
        emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"))
        return room_id

    # if the user isn't inside of any room, 
    # perhaps this user has recently left a room
    # or is simply a new user looking to chat with someone
    room_id = room.create_room(sender_name, receiver_name)
    join_room(room_id)
    emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"), to=room_id)
    return room_id

# leave room event handler
@socketio.on("leave")
def leave(username, room_id):
    emit("incoming", (f"{username} has left the room.", "red"), to=room_id)
    leave_room(room_id)
    room.leave_room(username)

@socketio.on("online")
def heartbeat_online(username):
    active_user = db.get_user(username)
    if active_user:
        active_user_friends = db.get_friends(active_user.username)
        main_sid = user_sessions[active_user.username]
        friends_session_ids = [user_sessions[x.username] for x in active_user_friends if x.username in user_sessions]

        # notify all friends that the user is online
        for friend_sid in friends_session_ids:
            emit("friend_online", {"username": username}, room=friend_sid)
        
        # notify the user of their friends' online statuses
        for friend in active_user_friends:
            if friend.username in user_sessions:
                emit("friend_online", {"username": friend.username}, room=main_sid)
    

@socketio.on("offline")
def heartbeat_offline(username):
    inactive_user = db.get_user(username)
    if inactive_user:
        inactive_user_friends = db.get_friends(inactive_user.username)
        friends_session_ids = [user_sessions[x.username] for x in inactive_user_friends if x.username in user_sessions]

        # notify all friends that user is offline
        for friend_sid in friends_session_ids:
            emit("friend_offline", {"username": username}, room=friend_sid)

##############
# ENCRYPTION #
##############

# @socketio.on("send_encrypted_key")
# def handle_send_encrypted_key(data):
#     room_id = data["room_id"]
#     encrypted_key = data["encrypted_key"]
#     sender = data["sender"]
#     print(f"Emitting encrypted key to room {room_id}: {encrypted_key}")
#     emit("receive_encrypted_key", {'encrypted_key': encrypted_key, 'sender': sender, 'room_id': room_id}, to=room_id)

# @socketio.on("finally")
# def letsgo(username):
#     sender_name = username
#     room_id = room.get_room_id(sender_name)
#     emit("incoming", (f"{sender_name} has joined the room. Ready for secure communication!", "green"), to=room_id)
#     emit("incoming", ("Now generating HMAC keys for both users.", "blue"), to=room_id)

#     # Generate a 16-byte salt
#     salt = os.urandom(16)
#     # Encode the salt in Base64 to make it easy to transmit and store
#     salt_encoded = base64.b64encode(salt).decode('utf-8')
    
#     # Emit the setupHMACKeys event with the salt
#     emit("setupHMACKeys", {'room_id': room_id, 'salt': salt_encoded}, to=room_id)

