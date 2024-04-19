To store messages sent to the database, you would typically use a database model. Here's an example of how you might define a `Message` model using SQLAlchemy, which is a popular ORM (Object-Relational Mapper) for Flask:

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.content}>'
```

In this example, each `Message` has an `id`, a `sender_id`, a `receiver_id`, `content`, and a `timestamp`. The `sender_id` and `receiver_id` are foreign keys that reference the `id` of a `User` in the `user` table.

You would use this model to store a new message like this:

```python
@socketio.on('message')
def handle_message(data):
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    content = data['content']
    message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.session.add(message)
    db.session.commit()
```

In this example, the `handle_message` function is triggered when a 'message' event is received from the client. It creates a new `Message` with the `sender_id`, `receiver_id`, and `content` from the data sent by the client, adds it to the database session, and commits the session to save the message in the database.