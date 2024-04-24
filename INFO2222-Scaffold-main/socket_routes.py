'''
socket_routes
file containing all the routes related to socket.io
'''


from flask_socketio import join_room, emit, leave_room
from flask import request
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
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    
    # calls js logout() function to clear cookies
    session_id = user_sessions[username]
    emit("logout", to=session_id)
    
    # removes user from session IDs to clean up
    username_to_remove = [user for user, sid in user_sessions.items() if sid == request.sid]
    for username in username_to_remove:
        del user_sessions[username]

    emit("incoming", (f"{username} has disconnected", "red"), to=int(room_id))

# send message event handler
@socketio.on("send")
def send(username, message, room_id):
    emit("incoming", (username, message), to=room_id) # to test, <script>alert('XSS Test');</script>

@socketio.on("safe-send")
def safe_send(username, message, room_id):
    print(message)
    emit("safe-incoming", (username, message), to=room_id)


# Template for the message event handler
########################################
# store message to database
# @socketio.on('message')
# def handle_message(data):
#     sender_id = data['sender_id']
#     receiver_id = data['receiver_id']
#     content = data['content']
#     message = Message(sender_id=sender_id,
#                       receiver_id=receiver_id, content=content)
#     db.session.add(message)
#     db.session.commit()
########################################

# join room event handler
# sent when the user joins a room
@socketio.on("join")
def join(sender_name, receiver_name):

    # user who initiated the join
    sender_name = sender_name.strip()

    # user invited to the join
    receiver_name = receiver_name.strip()
    
    # check if the sender & receiver exists
    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"
    
    # get the current room_ids of sender and receiver, if any
    sender_room_id = room.get_room_id(sender_name) # always be none at the start (right now theres a bug where it isnt, causing multiple joins at the start)
    receiver_room_id = room.get_room_id(receiver_name)

    # terminal logging
    print(f"Existing room: {sender_room_id}, room_id: {receiver_room_id}")

    # if user is already in a room, prompt to leave
    if sender_room_id is not None and sender_room_id != receiver_room_id:
        return "You are already in another room. Please leave it first."

    # if user is already in a room with them
    if sender_room_id and receiver_room_id and sender_room_id == receiver_room_id:
        if room.is_active(sender_name) and room.is_active(receiver_name):
            return "You are already connected with this user." 

    # if the receiver is not in a room, then sender creates a room, an allocates that room_id to both of them.
    # sender then joins that room.
    if receiver_room_id is None:
        receiver_room_id = room.create_room(room, sender_name, receiver_name) 
        join_room(receiver_room_id)
        emit("waiting", {"room_id": receiver_room_id, "receiver": receiver_name}, to=receiver_room_id)
        emit("incoming", (f"{sender_name} has joined the room. Waiting for {receiver_name} to join.", "green"), to=receiver_room_id)
    else:
        if not room.is_active(sender_name) and sender_room_id == receiver_room_id:
            room.join_room(sender_name, receiver_room_id)
            join_room(receiver_room_id)
            print(f"Emitting room_ready to room {receiver_room_id}, from {sender_name} with friendUsername {receiver_name}")
            emit("room_ready", {"room_id": receiver_room_id, "sender": sender_name, "receiver": receiver_name}, to=receiver_room_id)
    
    return receiver_room_id    

# leave room event handler
@socketio.on("leave")
def leave(username, room_id):
    emit("incoming", (f"{username} has left the room.", "red"), to=room_id)
    leave_room(room_id)
    room.leave_room(username)

@socketio.on("send_encrypted_key")
def handle_send_encrypted_key(data):
    room_id = data["room_id"]
    encrypted_key = data["encrypted_key"]
    sender = data["sender"]
    print(f"Emitting encrypted key to room {room_id}: {encrypted_key}")
    emit("receive_encrypted_key", {'encrypted_key': encrypted_key, 'sender': sender, 'room_id': room_id}, to=room_id)

@socketio.on("finally")
def letsgo(username):
    sender_name = username
    room_id = room.get_room_id(sender_name)
    emit("incoming", (f"{sender_name} has joined the room. Ready for secure communication!", "green"), to=room_id)
    emit("incoming", ("Now generating HMAC keys for both users.", "blue"), to=room_id)

    # Generate a 16-byte salt
    salt = os.urandom(16)
    # Encode the salt in Base64 to make it easy to transmit and store
    salt_encoded = base64.b64encode(salt).decode('utf-8')
    
    # Emit the setupHMACKeys event with the salt
    emit("setupHMACKeys", {'room_id': room_id, 'salt': salt_encoded}, to=room_id)


