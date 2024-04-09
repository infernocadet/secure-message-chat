# secure-message-chat
The most secure (and usable!) messaging application.

## marc's understanding

### ```app.py```

#### simple config

the ```secrets``` module is used to generate our cryptographically strong random number. 

lets break down a bunch of the lines:

```python
app = Flask(__name__)
```
create new ```Flask``` variable ```app```.

```python
app.config['SECRET_KEY'] = secrets.token_hex()
```
```secrets.token_hex()``` returns a random text string in hexadecimal, *nbytes* random bytes. 

in our ```app``` object, we can alter the configuration files. ```.config``` accesses the dictionary of configurations we can set, so we are changing the secret_key config. this secret key is used for securely signing the session cookie and can also be used for other security related to our app. documentation for configuration [here](https://flask.palletsprojects.com/en/2.3.x/config/)

```python
import socket_routes
```

this relates to a separate file in our project, ```socket_routes.py```. more on this later

#### ```@app.route```

```python
@app.route("/")
def index():
    return render_template("index.jinja")
```

```python
@app.route("/login")
def login():    
    return render_template("login.jinja")
```

this relates to **app routing**, which maps a URL to a specific function that will handle the logic for that URL. here, ```"/"``` refers to the root of our web app. we define an ```index()``` function which is now mapped with the root path and the output of the function is rendered on the browser.

we can even build dynamic URLs by using variables in the URL. e.g.:

```python
@app.route("/user/<username>")
def show_user(username):
    return f"Hello, {username}!"
```

```python
@app.route("/user")
def user_profile():
    return render_template("user.jinja")
```

more on ```render_template``` later, but in this case, we are showing the ```index.jinja``` file to the user.

```python
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
```

the comment on this function says ```"handles a post request when the user clicks the log in button"```. what is a **post** request? [HTTP](https://www.w3schools.com/tags/ref_httpmethods.asp) works as a request response protocol between client and server. a response will contain **status information** and **requested content**.

```POST``` is used to send data to a server to create/update a resource.

the ```request``` is a Python object, which is automatically created and encapsulates all the data that comes from an incoming HTTP request made by a client. it includes things like the URL path, query parameters, headers, and the body of the request.

in our ```login.jinja``` file, we have spaces for the user to input their username and password. in that file as well, the ```login``` button is connected to a ```login()``` function. inside this function, Axios is used to send a POST request to the server. the url for this request is obtained through the jinja file

```jinja
let loginURL = "{{ url_for('login_user') }}";
```

## Marc's Notes

### Adding friends and displaying a friends list

Essentially, we needed to figure out how we were to store other users as friends of current users. 

Let's take a look into our ```User``` class.

```python
# from models.py...
class User(Base):
    __tablename__ = "user"
 
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)

    friends: Mapped[List["User"]] = relationship(
        "User",
        secondary=friend_table,
        primaryjoin=username == friend_table.c.user_id,
        secondaryjoin=username == friend_table.c.friend_id,
        back_populates="friends"
    )
```

Now I've changed some things, but essentially I just added a ```friends``` attribute to the User class. A User has a username and password, which are mapped into columns. In our website logic, we can access the username and password of a user through these attributes. I also made another column, called friends, which holds a list of ```Users```, and references another table, called ```friend_table```. This is how we will store and reference the friends of a User.

```python
# from models.py...
friend_table = Table('friends', Base.metadata, 
    Column('user_id', String, ForeignKey('user.username'), primary_key=True),
    Column('friend_id', String, ForeignKey('user.username'), primary_key=True)
)
```

```friend_table``` has two columns which are both primary keys (i.e. they are composite keys), which means that every record is **unique** and **not null**. It essentially has the ```user_id```, which is a username, which points to the username in the main "user" table, and it does the same thing for friend too. 

Regarding the ```friends``` table under the ```User``` class, the ```friends``` attribute is defined to represent the many-to-many relationship between users.

It is a list of ```User``` objects. The primary and secondary joins essentially mean: *to find my friends, look for entries in ```friend_table``` where my ```username``` matches the ```user_id```. ```back_populates="friends"``` is a nice little trick which makes sure the relationship is bi-directional - if A adds B as a friend, B will automatically gain A as a friend. This will be helpful for friend request approval or rejection.

How do we handle this in our website? First we need a form:

```html
<!--from home.jinja-->
<!-- Friends form to add friends -->
<h1>Add friend</h1>
<form id="addFriendForm">
    <label for="friendUsername">Friend's Username:</label>
    <input id="friendUsername" name ="friendUsername" type="text" required />
    <button type="submit">Add Friend</button>
</form>
```
Here, we've made a form, which we can reference through its ```id```, ```addFriendForm```. The main thing here is th


```javascript
<aside id="friends_list">
    <h2>Friends</h2> 
    {% if friends %}
        <ul>
            {% set user_friends = friends %}
            {% for item in user_friends %}
            <li>{{ item.username }}</li>
            {% endfor %}
        </ul>
    {% else %}
        <p>It's a bit lonely in here...</p>
    {% endif %}
</aside>
```

This code here is pretty simple, it shows our friends list. Need to implement how to make this refresh automatically without the page having to reload. Maybe that is annoying

```python
# from app.py...
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
```

