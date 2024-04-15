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
