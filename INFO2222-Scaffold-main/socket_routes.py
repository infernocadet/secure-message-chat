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

# store message to the database
@socketio.on('store_message')
def store_message(data):
    username = data['username']
    room_id = data['room_id']
    cypher_text = data['cypher_text']
    iv = data['iv']

    # username = data.get('username')
    # receiver = data.get('receiver')
    # encrypted_message = data.get('encrypted_message')
    # iv = data.get('iv')

    if username and room_id and cypher_text and iv:
    
        new_message = db.Message(
            sender=username, receiver=room_id, cypher_text=cypher_text, iv=iv)

        db.session.add(new_message)
        db.session.commit()
        emit("message_stored", {"status": "success",
             "room_id": room_id}, to=room_id)

    else:
        emit("message_stored", {
             "status": "fail", "message": "Incomplete data received"}, to=room_id)


# join room event handler
# sent when the user joins a room
@socketio.on("join")
def join(sender_name, receiver_name):

    sender_name = sender_name.strip()
    receiver_name = receiver_name.strip()
    
    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    room_id = room.get_room_id(receiver_name)
    if room_id is None:
        room_id = room.create_room(sender_name, receiver_name) # sets sender as the initiator
        join_room(room_id)
        emit("waiting", {"room_id": room_id, "receiver": receiver_name}, to=room_id)
        emit("incoming", (f"{sender_name} has joined the room. Waiting for {receiver_name} to join.", "green"), to=room_id)
    else:
        room.join_room(sender_name, room_id)
        join_room(room_id)
        print(f"Emitting room_ready to room {room_id}, from {sender_name} with friendUsername {receiver_name}")
        emit("room_ready", {"room_id": room_id, "sender": sender_name, "receiver": receiver_name}, to=room_id)
    
    return room_id    

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


