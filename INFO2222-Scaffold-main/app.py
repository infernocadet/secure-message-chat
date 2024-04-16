'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, jsonify, redirect, flash
from flask import session as flask_session
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import timedelta
from functools import wraps
from sqlalchemy.orm import sessionmaker
import db
import secrets
from db import engine, Session, verify_password
from models import User, FriendRequest
from shared_state import user_sessions
from bleach import clean # for sanitizing user input

# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)
bcrypt = Bcrypt(app)
CORS(app)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
app.config['SESSION_COOKIE_SECURE'] = True # secure cookies only sent over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True # cookies not accessible over javascript
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
socketio = SocketIO(app)

# don't remove this!!
import socket_routes


# session class bound to the engine
Session = sessionmaker(bind=engine)

# sanitize user input
# you will see that i have used this function in the login and signup routes, and addfriend routes to sanitise any user data that is sent to the server
# jinja automatically escapes html attributes that return back to the client using the double curly braces {{ }} so we don't need to worry about that
def sanitize_input(input):
    return clean(input, strip=True, tags=[], attributes={}, styles=[])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in flask_session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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

    username = sanitize_input(request.json.get("username"))
    password = sanitize_input(request.json.get("password"))

    user =  db.get_user(username)
    
    if user is None:
        return jsonify({"error": f"User \"{username}\" does not exist."}), 404

    if not verify_password(user.password, password):
        return jsonify({"error": "Incorrect password."}), 409

    flask_session.clear()
    flask_session['username'] = username
    print(flask_session)

    # user was successful in logging in.
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

    username = sanitize_input(request.json.get("username"))
    password = sanitize_input(request.json.get("password"))

    if db.get_user(username) is None:
        db.insert_user(username, password)
        flask_session.clear()
        flask_session['username'] = db.get_user(username).username
        return url_for('home', username=username)
    return "Error: User already exists!"


# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404


# home page, where the messaging app is
@app.route("/home")
@login_required
def home():

    # get the current user's username from the request (cleaned)
    current_user_username = sanitize_input(request.args.get("username"))

    if current_user_username is None:
        abort(404)
    
    # check if the current user is the same as the user in the session
    try:
        if current_user_username != flask_session.get("username"):
            return redirect(url_for('login'))
    except Exception as e:
        print(e)
        return redirect(url_for('login'))

    db_session = Session()
    try:
        current_user = db_session.query(User).filter_by(username=current_user_username).first()
        if current_user is None:
            abort(404)
        
        friends = current_user.friends[:]

        incoming_friends = db_session.query(FriendRequest).filter(FriendRequest.receiver_id == current_user_username, FriendRequest.status == "pending").all()
        incoming_requests = [
            {
                'id': req.id,
                'sender_username': req.sender_id
            } for req in incoming_friends
        ]

        sent_requests = db_session.query(FriendRequest).filter(FriendRequest.sender_id == current_user_username, FriendRequest.status == "pending").all()
        sent_requests_list = [
            {
                'id': sent.id,
                'receiver_username': sent.receiver_id
            } for sent in sent_requests
        ]
    
    finally:
        db_session.close()

    return render_template("home.jinja", username=current_user_username, friends=friends, incoming_friends=incoming_requests, sent_requests=sent_requests_list)

@app.route("/add_friend", methods=['POST'])
@login_required
def add_friend():

    # check if the request is json
    if not request.is_json:
        abort(404)    
    
    # get the current username and friend username from the request
    current_user_username = sanitize_input(request.json.get("current_user"))
    friend_username = sanitize_input(request.json.get("friend_user"))

    try:
        if current_user_username != flask_session.get("username"):
            return redirect(url_for('login'))
    except Exception as e:
        print(e)
        return redirect(url_for('login'))

    db_session = Session()

    # get the User object for current user and friend user from database
    current_user = db_session.query(User).filter_by(username=current_user_username).first()
    friend_user = db_session.query(User).filter_by(username=friend_username).first()

    # check if the users exist
    if not current_user or not friend_user:
        db_session.close()
        return jsonify({"error": "user not found"}), 404

    # check if users are already friends
    if friend_user in current_user.friends:
        db_session.close()
        return jsonify({"error": f"You are already friends with {friend_username}."}), 409

    # check if the friend request already exists
    existing_request = db_session.query(FriendRequest).filter_by(sender_id=current_user_username, receiver_id=friend_username).first()
    if existing_request:
        db_session.close()
        return jsonify({"error": f"Friend request to {friend_username} has already been sent."}), 409

    # if no existing request, create a new friend request
    friend_request = FriendRequest(sender=current_user, receiver=friend_user, status='pending')
    db_session.add(friend_request)
    db_session.commit()
    
    # emit request event to recipient user 
    receiver_session_id = user_sessions.get(friend_username)

    if receiver_session_id:
        socketio.emit("update_friend_requests", {'new_friend': current_user_username, 'request_id': friend_request.id}, room=receiver_session_id)

    # emit sent event to sender user
    sender_session_id = user_sessions.get(current_user_username)

    if current_user_username:
        socketio.emit("update_sent_requests", {'receiver_username': friend_username, 'request_id': friend_request.id}, room=sender_session_id)

    db_session.close()
    return jsonify({"success": True}), 200


@app.route("/accept_friend_request", methods=['POST'])
@login_required
def accept_friend_request():

    if not request.is_json:
        abort(404)
    request_id = request.json.get("request_id")

    # get the current username from the session
    session_username = flask_session.get("username")
    
    db_session = Session()
    try:
        friend_request = db_session.query(FriendRequest).filter_by(id=request_id).first()

        if friend_request is None:
            db_session.close()
            return jsonify({"error": "Friend request not found"}), 404
        
        # check if the user is the receiver of the friend request
        if friend_request.receiver_id != session_username:
            db_session.close()
            return jsonify({"error": "You are not the receiver of this friend request"}), 403

        friend_request.status = "accepted"
        sender = friend_request.sender
        receiver = friend_request.receiver

        sender.friends.append(receiver)
        receiver.friends.append(sender)
        
        db_session.delete(friend_request)
        db_session.commit()

        # Emit update to both users
        # find socket session ID for sender and receiver
        sender_session_id = user_sessions.get(sender.username)
        receiver_session_id = user_sessions.get(receiver.username)

        # emit an update to sender
        if sender_session_id:
            socketio.emit("update_friends_list", {'new_friend': receiver.username}, room=sender_session_id)
            socketio.emit("update_sent_requests_status", {'request_id': request_id, 'new_status': friend_request.status}, room=sender_session_id)
        
        # emit an update to receiver
        if receiver_session_id:
            socketio.emit("update_friends_list", {'new_friend': sender.username}, room=receiver_session_id)


        return jsonify({"success": "Friend request accepted", "newFriendUsername": sender.username}), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db_session.close()



@app.route("/reject_friend_request", methods=['POST'])
def reject_friend_request():

    if not request.is_json:
        abort(404)
    request_id = request.json.get("request_id")

    # get the current username from the session
    session_username = flask_session.get("username")
    
    db_session = Session()
    try:
        friend_request = db_session.query(FriendRequest).filter_by(id=request_id).first()

        if friend_request is None:
            return jsonify({"error": "Friend request not found"}), 404
        
        # check if the user is the receiver of the friend request
        if friend_request.receiver_id != session_username:
            db_session.close()
            return jsonify({"error": "You are not the receiver of this friend request"}), 403

        # session.delete(friend_request)
        friend_request.status = "rejected"
        db_session.commit()

        # emit an update to sender
        sender = friend_request.sender
        sender_session_id = user_sessions.get(sender.username)
        if sender_session_id:
            socketio.emit("update_sent_requests_status", {'request_id': request_id, 'new_status': friend_request.status}, room=sender_session_id)

        return jsonify({"success": "Friend request rejected"}), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db_session.close()

# route to logout
@app.route("/logout")
def logout():
    flask_session.clear()
    return redirect(url_for('index'))    


@app.after_request
def add_security_headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
        

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=("mycerts/smc.test.crt", "mycerts/smc.test.key"))
