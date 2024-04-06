'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, jsonify
from flask_socketio import SocketIO
from sqlalchemy.orm import sessionmaker
import db
import secrets
from db import engine, Session
from models import User, FriendRequest

# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# session class bound to the engine
Session = sessionmaker(bind=engine)

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")

    user =  db.get_user(username)
    if user is None:
        return "Error: User does not exist!"

    if user.password != password:
        return "Error: Password does not match!"

    return url_for('home', username=request.json.get("username"))


# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    password = request.json.get("password")

    if db.get_user(username) is None:
        db.insert_user(username, password)
        return url_for('home', username=username)
    return "Error: User already exists!"

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
def home():
    current_user_username = request.args.get("username")
    if current_user_username is None:
        abort(404)

    session = Session()
    try:
        current_user = session.query(User).filter_by(username=current_user_username).first()
        if current_user is None:
            abort(404)
        
        friends = current_user.friends[:]

        incoming_friends = session.query(FriendRequest).filter(FriendRequest.receiver_id == current_user_username, FriendRequest.status == "pending").all()
        incoming_requests = [
            {
                'id': req.id,
                'sender_username': req.sender_id
            } for req in incoming_friends
        ]

        sent_requests = session.query(FriendRequest).filter(FriendRequest.sender_id == current_user_username, FriendRequest.status == "pending").all()
        sent_requests_list = [
            {
                'id': sent.id,
                'receiver_username': sent.receiver_id
            } for sent in sent_requests
        ]
    
    finally:
        session.close()

    return render_template("home.jinja", username=current_user_username, friends=friends, incoming_friends=incoming_friends, sent_requests=sent_requests_list)

@app.route("/add_friend", methods=['POST'])
def add_friend():
    if not request.is_json:
        abort(404)    
    current_user_username = request.json.get("current_user")
    friend_username = request.json.get("friend_user")

    session = Session()

    # get the User object for current user and friend user from database
    current_user = session.query(User).filter_by(username=current_user_username).first()
    friend_user = session.query(User).filter_by(username=friend_username).first()

    if not current_user or not friend_user:
        session.close()
        return jsonify({"error": "user not found"}), 404
    
    friend_request = FriendRequest(sender=current_user, receiver=friend_user, status='pending')
    session.add(friend_request)
    session.commit()
    session.close()
    return jsonify({"success": True}), 200


@app.route("/accept_friend_request", methods=['POST'])
def accept_friend_request():

    if not request.is_json:
        abort(404)
    request_id = request.json.get("request_id")
    
    session = Session()
    try:
        friend_request = session.query(FriendRequest).filter_by(id=request_id).first()

        if friend_request is None:
            return jsonify({"error": "Friend request not found"}), 404

        # TODO: Check if the current user (from session or token) is the receiver of the friend request
        # This makes sure that actions are authenticated

        friend_request.status = "accepted"
        sender = friend_request.sender
        receiver = friend_request.receiver

        sender.friends.append(receiver)
        receiver.friends.append(sender)
        
        session.delete(friend_request)
        session.commit()
        return jsonify({"success": "Friend request accepted"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()



@app.route("/reject_friend_request", methods=['POST'])
def reject_friend_request():

    if not request.is_json:
        abort(404)
    request_id = request.json.get("request_id")
    
    session = Session()
    try:
        friend_request = session.query(FriendRequest).filter_by(id=request_id).first()

        if friend_request is None:
            return jsonify({"error": "Friend request not found"}), 404
        
        # TODO: Check if the current user (from session or token) is the receiver of the friend request
        # This makes sure that actions are authenticated
        # Then we can delete the friend request too if we want. but if we see if a previous request was rejected
        # then maybe we can stop further invitations

        # session.delete(friend_request)
        friend_request.status = "rejected"
        session.commit()
        return jsonify({"success": "Friend request rejected"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()

        

if __name__ == '__main__':
    socketio.run(app)
