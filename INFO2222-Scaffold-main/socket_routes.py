'''
socket_routes
file containing all the routes related to socket.io
'''


from flask_socketio import join_room, emit, leave_room
from flask import request
from bleach import clean 

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
    sanitised_message = clean(message)
    emit("incoming", (f"{username}: {sanitised_message}"), to=room_id) # to test, <script>alert('XSS Test');</script>
    
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

    # # check if both participants are in the room
    # participants = [user for user, rid in room.dict.items() if rid == room_id]
    # if len(participants) == 2:
    #     print(f"Sockets sees two people in here: {participants[0]} and {participants[1]}")
    #     initiator = room.get_initiator(room_id)
        
    # else:
    #     emit("incoming", (f"{sender_name} has joined the room. Waiting for {receiver_name} to join.", "green"), to=room_id)
    
    # return room_id
    
    # if the user is already inside of a room 
    # if room_id is not None:
        
    #     room.join_room(sender_name, room_id)
    #     join_room(room_id)
    #     # emit to everyone in the room except the sender
    #     emit("incoming", (f"{sender_name} has joined the room.", "green"), to=room_id, include_self=False)
    #     # emit only to the sender
    #     emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"))
    #     return room_id

    # if the user isn't inside of any room, 
    # perhaps this user has recently left a room
    # or is simply a new user looking to chat with someone
    
    
    

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
