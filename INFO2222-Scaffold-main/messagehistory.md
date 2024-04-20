Your concept for implementing secure message storage in a way that the server doesn't have access to the plaintext messages is a solid approach for preserving privacy and security. Let’s break down the implementation into steps and explore the necessary considerations and potential solutions:

1. Symmetric Key Derivation
To securely store messages on a server without exposing their contents, you can derive a symmetric key from the user’s password each time they log in. This can be achieved using PBKDF2, a key derivation function, with a user-specific salt stored securely on the server but never exposed to anyone but the user.

2. Encrypting and Decrypting Messages
Before storing a message in the database:

Encrypt the message using the derived symmetric key whenever a user sends or receives a message.
Use AES-GCM for encryption to ensure confidentiality and integrity of the messages.
After retrieving a message from the database:

Decrypt the message using the same symmetric key derived at login.
3. Database Schema
You can structure the database such that each user has a table or a collection of messages where each entry includes:

Room ID or Recipient's Username: To identify the chat session.
Encrypted Message: The content of the message after encryption.
Timestamp: To maintain the order of messages.
4. Server-Side Implementation
On the server, handle the storage and retrieval of encrypted messages. Ensure that all operations concerning the handling of plaintext messages happen on the client side. The server should only receive and send back encrypted data.

Implementation Steps:
Deriving the Key
Each time a user logs in, derive the encryption key from their password:

```js
async function deriveKeyFromPassword(password, salt) {
    const encoder = new TextEncoder();
    const keyMaterial = await window.crypto.subtle.importKey(
        "raw",
        encoder.encode(password),
        { name: "PBKDF2" },
        false,
        ["deriveKey"]
    );

    return window.crypto.subtle.deriveKey(
        {
            name: "PBKDF2",
            salt: salt,
            iterations: 100000,
            hash: "SHA-256"
        },
        keyMaterial,
        { name: "AES-GCM", length: 256 },
        true,
        ["encrypt", "decrypt"]
    );
}
```

Encrypting Messages
Encrypt messages before sending them to the server for storage:
    
```js
async function encryptMessage(message, key) {
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const encoder = new TextEncoder();
    const encoded = encoder.encode(message);
    const encrypted = await window.crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, encoded);

    return {
        iv: Array.from(iv),
        data: btoa(String.fromCharCode(...new Uint8Array(encrypted)))
    };
}
```

Decrypting Messages
Decrypt messages retrieved from the server:

```js
async function decryptMessage(encryptedObj, key) {
    const iv = new Uint8Array(encryptedObj.iv);
    const encrypted = new Uint8Array(atob(encryptedObj.data).split('').map(char => char.charCodeAt(0)));

    const decrypted = await window.crypto.subtle.decrypt({ name: "AES-GCM", iv }, key, encrypted);
    const decoder = new TextDecoder();
    return decoder.decode(decrypted);
}
```


Great! Now that you're considering integrating a message history feature that encrypts messages before storage, using SQLAlchemy is a good choice for managing relational data in Python. Let's build on the existing structure and add the necessary components to handle encrypted message storage securely:

1. Adjusting the Message Model
You need to adjust the Message model to include fields for storing encrypted messages, the IV (Initialization Vector), and potentially any other metadata needed for decryption, such as a timestamp or nonce if they're not included in the encrypted payload:

```python
class Message(Base):
    __tablename__ = "message"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str] = mapped_column(String, ForeignKey('user.username'))
    receiver: Mapped[str] = mapped_column(String, ForeignKey('user.username'))
    encrypted_message: Mapped[str] = mapped_column(Text)  # Store the encrypted message content
    iv: Mapped[str] = mapped_column(Text)  # Store the IV needed for decryption
    timestamp: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow)  # Optional
```

2. Encrypt and Decrypt Messages
To handle encryption and decryption securely, you can use a symmetric key derived from the user's password each time they log in. This key should never be stored persistently but re-derived at each session:

Client-side Encryption before Sending to Server:
```python
async function encryptAndStoreMessage(message, room_id, symKey) {
    const { cipherText, iv } = await encryptMessage(message, symKey);
    // Send encrypted message and iv to the server
    socket.emit("store_message", { room_id, cipherText, iv });
}
```

Client-side Decryption after Retrieving from Server:
```python
async function decryptMessageHistory(messages, symKey) {
    return Promise.all(messages.map(async (msg) => {
        const decryptedText = await decryptMessage(msg.encrypted_message, symKey, msg.iv);
        return { ...msg, decryptedText };
    }));
}
```

3. Storing and Retrieving Messages
Implement routes or socket events in your server-side code to handle storing and retrieving these encrypted messages:

Server-side Store Message Handler:
```python
@socketio.on("store_message")
def handle_store_message(data):
    username = data['username']
    room_id = data['room_id']
    encrypted_message = data['cipherText']
    iv = data['iv']
    
    new_message = Message(sender=username, receiver=get_receiver_from_room(room_id),
                          encrypted_message=encrypted_message, iv=iv)
    db.session.add(new_message)
    db.session.commit()
    emit("message_stored", {"status": "success", "room_id": room_id}, to=room_id)
```

Server-side Fetch Message History:
```python
@app.route('/get_messages/<room_id>')
def get_messages(room_id):
    messages = Message.query.filter_by(room_id=room_id).all()
    return jsonify([{"sender": msg.sender, "encrypted_message": msg.encrypted_message, "iv": msg.iv, "timestamp": msg.timestamp.isoformat()} for msg in messages])
```

4. Security Considerations
Ensure the symmetric key is securely derived and never stored in plaintext.
Use a secure session management strategy to protect user sessions.
Consider adding HMAC to verify the integrity and authenticity of the stored messages upon retrieval.
This setup ensures that message contents are protected against unauthorized access, including from the server operators, and provides a basis for secure message retrieval and display in historical chat contexts.