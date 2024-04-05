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
from models import User

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
    
    finally:
        session.close()

    return render_template("home.jinja", username=current_user_username, friends=friends)

@app.route("/add_friend", methods=['POST'])
def add_friend():
    if not request.is_json:
        abort(404)    
    current_user_username = request.json.get("current_user")
    friend_username = request.json.get("friend_user")

    session = Session()

    current_user = session.query(User).filter_by(username=current_user_username).first()
    friend_user = session.query(User).filter_by(username=friend_username).first()

    if not current_user or not friend_user:
        session.close()
        return jsonify({"error": "user not found"}), 404
    
    current_user.friends.append(friend_user)
    friend_user.friends.append(current_user)

    session.commit()
    session.close()
    return jsonify({"success": True}), 200

if __name__ == '__main__':
    socketio.run(app)
