# Encryption Roadmap

In this document, we will outline the steps required to implement message encryption in our messaging app.

## Table of Contents

1. [Introduction](#introduction)
2. [Step 1: Key Generation](#step-1-key-generation)
3. [Step 2: Message Encryption](#step-2-message-encryption)
4. [Step 3: Message Decryption](#step-3-message-decryption)
5. [Conclusion](#conclusion)

## Introduction

In order to ensure the security and privacy of our users' messages, we need to implement encryption. This will protect the content of the messages from unauthorized access. This is called end-to-end encryption (E2EE). The server will act as a middleman to pass encrypted messages, which it cannot decrypt.

Our basic outline:

1. **Key Generation**: When a user creates an account or during first login, generate a public-private key pair on the client-side. The private key must be securely stored on the client-side, and never exposed to the server or other clients. The public key can be shared with other users, and stored on the server.
2. **Key Exchange**: When a user initiates a chat with another user, their client should retrieve the recipients public key from the server. Similarly, the recipient retrieves the sender's public key. This allows both parties to encrypt messages that only the other party can decrypt, using their ***private key***.
3. **Encryption**: Before sending a message, the sender's client encrypts the message using the recipients public key. Only the recipient's private key can decrypt the message.
4. **Transmission**: Encrypted message is sent to the server, which forwards it to the recipient.
5. **Decryption**: Recipient's client receives message and uses recipient's private key to decrypt it.
6. **Secure Storage**: Done later, messages must remain encrypted on the server.

To implement in JavaScript, use the ```Web Cryptography API```.

## Step 1: Key Generation

The first step in the encryption process is to generate encryption keys. These keys will be used to encrypt and decrypt the messages. We need to carefully design a secure key generation algorithm to ensure the strength of the encryption.

1. **Using Web Cryptography API, generate a public-private key pair**: This API provides cryptographic operations which run in a secure context. We can generate keys that can be marked as ***non-extractable***, meaning they cannot be read or exported by the browser, only used for cryptographic operations.
2. **IndexedDB**: Store the public-private key pair in IndexedDB, which is a low-level API for client-side storage of data. 

Provided by ChatGPT:

```javascript
// This function generates a key pair and stores it in IndexedDB
function generateAndStoreKeyPair() {
  // Generate the key pair
  window.crypto.subtle.generateKey(
    {
      name: "RSA-OAEP",
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: { name: "SHA-256" },
    },
    true,
    ["encrypt", "decrypt"]
  )
  .then((keyPair) => {
    // Open a database
    const request = indexedDB.open("key-database", 1);

    request.onupgradeneeded = function(event) {
      const db = event.target.result;

      // Create an object store named 'keys'
      const objectStore = db.createObjectStore("keys", { keyPath: "id" });
      objectStore.transaction.oncomplete = function(event) {
        // Store the key in the new object store
        const keyObjectStore = db.transaction("keys", "readwrite").objectStore("keys");
        keyObjectStore.add({ id: "privateKey", key: keyPair.privateKey });
        keyObjectStore.add({ id: "publicKey", key: keyPair.publicKey });
      };
    };

    request.onerror = function(event) {
      console.error("Database error: " + event.target.errorCode);
    };

    // You should handle the successful addition of the key here
  })
  .catch((err) => {
    console.error(err);
  });
}

// Call this function to initiate key generation and storage
generateAndStoreKeyPair();
```

Let's take a look into the ```generateAndStoreKeyPair()``` function:
The ```window.crypto.subtle.generateKey``` method, which is part of the Web Cryptography API, generates a new key pair. We specify the algorithm to be used, in this case, RSA-OAEP with a modulus length of 2048 bits and SHA-256 hashing. The key pair is generated with the ability to encrypt and decrypt data. ```Extractable``` is set to ```true``` so that we can extract the key from the ```CryptoKey``` object later. 

The .then((keyPair) => {...}) is executed upon successful generation of keys. Now we store the generated keys in IndexedDB.

```const request = indexedDB.open("key-database", 1);``` opens a version of a database called ```"key-database"```. If it doesnt exist, i.e., ```request.onupgradeneeded```, this creates the table. Inside this request, and object store is created. I don't really get this part but this store has a keyPath of "id", which acts as a primary key for the data stored in this object store. Then an ```oncomplete``` event is triggered, and this adds the private and public keys to the store with identifiers privateKey and publicKey. 

## Step 2: Message Encryption

Once the encryption keys are generated, we can proceed with encrypting the messages. This involves converting the plain text message into a cipher text using the encryption algorithm and the generated keys. The encrypted message will be sent over the network.

## Step 3: Message Decryption

On the receiving end, the encrypted message needs to be decrypted to retrieve the original plain text. This requires using the decryption algorithm and the corresponding decryption keys. Only authorized recipients should have access to these keys.

## Conclusion

By following these steps, we can ensure that our messaging app provides secure and private communication for our users. Encryption plays a crucial role in protecting sensitive information from unauthorized access.

> user A starts a room
> user B joins the room
> user A creates a symmetric key and stores it for themselves
> user A encrypts the symmetric key with user B's public key
> user A sends the encrypted symmetric key to user B
> user B retrieves the encrypted symmetric key
> user B decrypts the symmetric key with their private key
> user B emits a "done" event to the room

> triggers a "setupHMAC" event for both users
> user A and User B create HMAC Key
> HMAC key is derived from the symmetric key
> HMAC key is stored for both users
> avoids unnecessary key exchange - less attack surface

# MESSAGE HISTORY
Currently having trouble figuring out how to implement message history due to the way we've implemented encryption for the chatroom.
When a user signs up, they generate their own public/private key pair - this stays with them for their account. The public key is stored on the server database, and private key stored in IndexedDB. 
When User A initiates a chatroom with User B, it waits for User B to join.
When User B joins, User A generates a symmetric key and encrypts it with User B's public key. User B decrypts the symmetric key with their private key. 
User A and User B both store this symmetric key in an IndexedDB database, and use it to encrypt and decrypt messages sent on the server. These messages are also encrypted with a randomly generated IV.
A HMAC key is also derived from the symmetric key and stored for both users in the IndexedDB database.
This way, both users can calculate the HMAC of the ciphertext and attach it to the sent message, and then both users can also correctly recalculate the HMAC to verify the integrity and authenticity of the message.

We are currently not too sure about how to implement message history. Is encrypting the chatroom with a symmetric key ideal? 

> user A clicks on User B
> creates a room with User A and User B in it 
> symmetric key exchange occurs
  > user A generates a random symmetric key when User B joins
  > exchange and decryption of symmetric key
  > user A and user B store these keys
> hmac key generation occurs
  > derived from the symmetric key
  > user A and user B store these keys
> when a user opens a chatroom session (initiates a previous chat with another user)
  > message history should pop up
  > message history should be stored, encrypted on the server
  > message history is decrypted using PASSWORD or key derived from password
> messages are already encrypted via symmetric key.
> monday: user A and user B open a chatroom
> tuesday: user A and user B open a chatroom
> symKey A != symKey B

> when a user is in a room, and they click on someone else
  > leave current room, make new one with other user
> id associated with the room based on who is in the room