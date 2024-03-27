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

we can even build dynamic URLs by using variables in the URL. 
e.g.
```python
@app.route("/user/<username>")
def show_user(username):
    return f"Hello, {username}!"
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

the comment on this function says ```"handles a post request when the user clicks the log in button"```. what is a **post** request? [HTTP](https://www.w3schools.com/tags/ref_httpmethods.asp) works as a request