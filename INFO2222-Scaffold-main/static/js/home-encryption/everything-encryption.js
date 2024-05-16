// This document contains everything to do with encryption from the home page

// this initialises the database

let db;

// Open connection to the IndexedDB
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open("CryptoKeys", 3);

        request.onerror = function(event) {
            console.error("Database error: " + event.target.errorCode);
            reject("Failed to open DB");
        };

        request.onsuccess = function(event) {
            db = event.target.result;
            resolve(db);
        };

        request.onupgradeneeded = function(event) {
            const db = event.target.result;
            if (!db.objectStoreNames.contains("PrivateKeyStore")) {
                db.createObjectStore("PrivateKeyStore", { keyPath: "id" });
            }
            if (!db.objectStoreNames.contains("SymmetricKeys")) {
            db.createObjectStore("SymmetricKeys", { keyPath: "id" });
            }
            if (!db.objectStoreNames.contains("HMACKeys")) {
            db.createObjectStore("HMACKeys", { keyPath: "id" });
            }
        };
    });
}


// Retrieve private key for a username
async function getPrivateKey(username) {
    console.log(username + " is attempting to get private key")

    if (!db){
        db = await openDB();
    }
     if (!db) {
        console.error("Database is not open");
        return;
    }

    return new Promise((resolve, reject) => {
        const transaction = db.transaction(["PrivateKeyStore"], "readonly");
        const store = transaction.objectStore("PrivateKeyStore");
        const request = store.get(username);

        request.onsuccess = async () => {
            if (request.result) {
                console.log("Private key found:", username);

                try {
                    // Import the key from the JWK format
                    const cryptoKey = await window.crypto.subtle.importKey(
                        "jwk",
                        JSON.parse(request.result.key), // Parse the stored string back into JSON
                        {
                            name: "RSA-OAEP",
                            hash: { name: "SHA-256" },
                        },
                        false, // whether the key is extractable (i.e., can be taken out of the web crypto API)
                        ["decrypt"] // this key can only be used to decrypt
                    );
                    resolve(cryptoKey);
                } catch (error) {
                    console.error("Error importing key:", error);
                    reject(error);
                }
            } else {
                console.log("No private key stored for", username);
                resolve(null);
            }
        };
        request.onerror = () => {
            console.error("Error fetching private key from IndexedDB.");
            reject("Failed to retrieve key");
        };
    });
}

// generate symmetric key used to ENCRYPT ALL THE MESSAGES
async function generateSymmetricKey(room_id){
    const key = await window.crypto.subtle.generateKey(
        {
            name: "AES-GCM",
            length: 256
        },
        true,
        ["encrypt", "decrypt"]
    );

    // store key in IndexedDB
    const keyData = await window.crypto.subtle.exportKey("jwk", key);
    const db = await openDB();
    const transaction = db.transaction(["SymmetricKeys"], "readwrite");
    const store = transaction.objectStore("SymmetricKeys");
    await store.put({id: room_id, key: keyData})

    // logging key data
    const jwkString = JSON.stringify(keyData);
    console.log("[SYMMETRIC KEY GENERATED]:", jwkString);

    // now send the key off to be encrypted and broadcasted to the room
    return key;
}

// encrypt the symmetric key using the receiver's public key
async function encryptSymmetricKey(key, publicKey){
    const exportedKey = await window.crypto.subtle.exportKey(
        "raw",
        key
    );
    const encryptedKey = await window.crypto.subtle.encrypt(
        {
            name: "RSA-OAEP"
        },
        publicKey,
        exportedKey
    );
    return encryptedKey;
}

// function to fetch the public key of a user
async function fetchPublicKey(username){
    try {
        let response = await axios.get(`/get_public_key/${username}`);
        return response.data.public_key;
    } catch (error) {
        console.error('Error fetching public key:', error);
        return null;
    }
}

// function to decrypt the encrypted symmetric key
async function decryptSymmetricKey(encryptedKey) {
    // get the private key
    console.log(username + " is attempting to decrypt symmetric key")
    const privateKey = await getPrivateKey(username);
    // decrypt the key
    console.log("attempting to decrypt key NOW")
    const decryptedKey = await window.crypto.subtle.decrypt(
        {
            name: "RSA-OAEP"
        },
        privateKey,
        encryptedKey
    );
    return decryptedKey;
}

// whenever we encrypt or decrypt messages, get the symmetric key
async function getSymmetricKey(room_id){
    const db = await openDB();
    const transaction = db.transaction(["SymmetricKeys"], "readonly");
    const store = transaction.objectStore("SymmetricKeys");
    const request = store.get(room_id);
    return new Promise((resolve, reject) => {
        request.onsuccess = () => {
            if (request.result) {
                resolve(window.crypto.subtle.importKey(
                    "jwk",
                    request.result.key,
                    {
                        name: "AES-GCM",
                        length: 256
                    },
                    true,
                    ["encrypt", "decrypt"]
                ));
            } else {
                reject("No key found");
            }
        };
        request.onerror = () => {
            reject("Failed to retrieve key");
        };
    });
}

// Helper function to convert a base64 string to ArrayBuffer
function base64ToArrayBuffer(base64) {
    var binary_string = window.atob(base64);
    var len = binary_string.length;
    var bytes = new Uint8Array(len);
    for (var i = 0; i < len; i++)        {
        bytes[i] = binary_string.charCodeAt(i);
    }
    return bytes.buffer;
}

// function to derive a HMAC key from the symmetric key
async function deriveHMACKey(symmetricKey, salt) {
    // export key to raw format
    const keyRaw = await window.crypto.subtle.exportKey("raw", symmetricKey);

    // import raw key as a format for PBKDF2
    const baseKey = await window.crypto.subtle.importKey(
        "raw",
        keyRaw,
        { name: "PBKDF2" },
        false,
        ["deriveKey"]
    );

    // define pbkdf2 parameters
    const iterations = 50000; // Higher is more secure but more computationally expensive
    const deriveParams = {
        name: "PBKDF2",
        salt: salt,
        iterations: iterations,
        hash: "SHA-256"
    };

    // derive the HMAC key
    const hmacKey = await window.crypto.subtle.deriveKey(
        deriveParams,
        baseKey,
        { name: "HMAC", hash: {name: "SHA-256"}, length: 256 },
        true, // set to true if you need to export the HMAC key
        ["sign", "verify"]
    );

    return hmacKey;
}

// function set up HMACkey in Storage
async function setupHMACKey(symmetricKey, room_id, salt) {
    try {
        const hmacKey = await deriveHMACKey(symmetricKey, salt);
        console.log("HMAC Key Derived and Ready for use.");

        // Export the HMAC key if you need to store it
        const exportedHmacKey = await window.crypto.subtle.exportKey("jwk", hmacKey);

        // Store the exported key in IndexedDB
        const db = await openDB();
        const transaction = db.transaction(["HMACKeys"], "readwrite");
        const store = transaction.objectStore("HMACKeys");
        await store.put({id: room_id, key: JSON.stringify(exportedHmacKey)}); // Store as string

        console.log("HMAC key stored in IndexedDB successfully");
    } catch (error) {
        console.error("Error deriving and storing HMAC key:", error);
    }
}

// function to retrieve HMACKey from storage
async function getHMACKey(room_id) {
    const db = await openDB();
    const transaction = db.transaction(["HMACKeys"], "readonly");
    const store = transaction.objectStore("HMACKeys");
    const request = store.get(room_id);

    return new Promise((resolve, reject) => {
        request.onsuccess = async () => {
            if (request.result) {
                try {
                    const hmacKey = await window.crypto.subtle.importKey(
                        "jwk",
                        JSON.parse(request.result.key), // Convert from string to JWK object
                        { name: "HMAC", hash: {name: "SHA-256"} },
                        true,
                        ["sign", "verify"]
                    );
                    resolve(hmacKey);
                } catch (error) {
                    console.error("Error importing HMAC key:", error);
                    reject(error);
                }
            } else {
                console.log("No HMAC key stored for room", room_id);
                reject("Key not found");
            }
        };
        request.onerror = () => {
            console.error("Error fetching HMAC key from IndexedDB.");
            reject("Failed to retrieve key");
        };
    });
}

// function to encrypt messages using AES-GCM
async function encryptMessage(message, symKey) {
    const encoder = new TextEncoder();
    const encodedMessage = encoder.encode(message);

    // generate a random IV for each encryption
    const iv = window.crypto.getRandomValues(new Uint8Array(12));

    const encryptedMessage = await window.crypto.subtle.encrypt(
        {
            name: "AES-GCM",
            iv: iv
        },
        symKey,
        encodedMessage
    );

    // convert arraybuffer to base64
    const cipherText = btoa(String.fromCharCode(...new Uint8Array(encryptedMessage)));

    return { cipherText, iv };
}

// function to decrypt messages using AES-GCM
async function decryptMessage(cipherText, iv, symKey) {
    const decoder = new TextDecoder();
    const encryptedBuffer = Uint8Array.from(atob(cipherText), c => c.charCodeAt(0));

    const decryptedContent = await window.crypto.subtle.decrypt(
        {
            name: "AES-GCM",
            iv: iv
        },
        symKey,
        encryptedBuffer
    );

    const decryptedMessage = decoder.decode(decryptedContent);
    return decryptedMessage;
}

// function to sign a message using HMAC
async function signMessage(data, hmacKey) {
    const encoder = new TextEncoder();
    const dataEncoded = encoder.encode(data);

    const hmacBuffer = await window.crypto.subtle.sign(
        "HMAC",
        hmacKey,
        dataEncoded
    );

    // convert the hmac buffer to a hex string for transmission
    return Array.from(new Uint8Array(hmacBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
}

// function to verify a message using HMAC
async function verifyHMAC(data, hmac, hmacKey){
    const valid = await window.crypto.subtle.verify(
        "HMAC",
        hmacKey,
        new Uint8Array(hmac.match(/[\da-f]{2}/gi).map(h => parseInt(h, 16))),
        new TextEncoder().encode(data)
    );
    return valid;
}

// we'll send the message to the server by emitting a "send" event
async function send() {
    let message = $("#message").val();
    $("#message").val("");
    if (message.trim() === "") return; // Prevent sending empty messages

    const symKey = await getSymmetricKey(room_id);
    const hmacKey = await getHMACKey(room_id);

    if (!symKey || !hmacKey) {
        console.error("Keys are not available to encrypt or sign the message.");
        return;
    }

    const { cipherText, iv } = await encryptMessage(message, symKey);
    const hmac = await signMessage(cipherText + iv, hmacKey);

    socket.emit("safe-send", username, { cipherText, iv: Array.from(iv), hmac }, room_id);  
} 

// listen for the encrypted key. after decrytion, the symmetric key is stored in the IndexedDB
socket.on("receive_encrypted_key", async function(data) {
    const sender = data.sender;
    const room_id = data.room_id;
    
    // only the receiver should store the key
    if (sender === username) {
        // get the encrypted key
        const encryptedKey = data.encrypted_key;

        console.log("Received encrypted key:", encryptedKey);

        try {
            const symmetricKeyRAW = await decryptSymmetricKey(encryptedKey);
            console.log("Symmetric key decrypted RAW DATA:", new Uint8Array(symmetricKeyRAW));

            // reimport raw key data to cryptokey object
            const symmetricKey = await window.crypto.subtle.importKey(
                "raw",
                symmetricKeyRAW,
                {
                    name: "AES-GCM",
                    length: 256
                },
                true,
                ["encrypt", "decrypt"]
            );

            // convert cryptokey back to JWK for storage
            const keyData = await window.crypto.subtle.exportKey("jwk", symmetricKey);
            console.log("Re-imported symmetric key: " + keyData);

            const db = await openDB();
            const transaction = db.transaction(["SymmetricKeys"], "readwrite");
            const store = transaction.objectStore("SymmetricKeys");
            await store.put({id: room_id, key: keyData});

            console.log("Symmetric key stored in IndexedDB successfully");
            socket.emit("finally", username);
        } catch (error) {
            console.error("Failed to decrypt symmetric key:", error);
        }
    } else {
        return;
    }    
});

// write a socket listener which listens for setupHMACKeys event, to call the setupHMACKey function (broadcasted to all users in room)
socket.on("setupHMACKeys", async function(data) {

    const room_id = data.room_id;
    const salt = Uint8Array.from(atob(data.salt), c => c.charCodeAt(0));
    const current_username = username
    console.log(username + " from Room " + room_id + " has received setupHMACKeys event.");
    try {
        const symKey = await getSymmetricKey(room_id);
        if (!symKey) {
            console.error("Symmetric key not found. Cannot set up HMAC key.");
            return;
        }
        console.log(current_username + ": Retrieved symmetric key. Now setting up HMAC key.")
        await setupHMACKey(symKey, room_id, salt);
    } catch (error) {
        console.error("Failed to set up HMAC key", error)
    }
});

//listen for room readiness before emitting join request
socket.on("room_ready", async function(data) {
    console.log(username + " received room_ready event");
    if (data.room_id === room_id && username === data.receiver) {

        console.log(username + "Generating symmetric key");
        const symmetricKey = await generateSymmetricKey(data.room_id);
        console.log(username + 'Symmetric key generated' + symmetricKey);

        console.log(username + 'Fetching public key from: ' + data.sender + '...');
        const publicKeyResponse = await fetchPublicKey(data.sender);
        if (!publicKeyResponse) {
            console.error('Failed to fetch public key');
            return;
        }
        const publicKeyData = base64ToArrayBuffer(publicKeyResponse);
        const publicKey = await window.crypto.subtle.importKey("spki", publicKeyData, { name: "RSA-OAEP", hash: "SHA-256" }, true, ["encrypt"]);
        const encryptedKey = await encryptSymmetricKey(symmetricKey, publicKey);

        console.log("Sending encrypted key from: " + username + " to: " + data.sender + " in room: " + data.room_id + " encrypted key: " + encryptedKey);
        socket.emit("send_encrypted_key", {room_id: data.room_id, encrypted_key: encryptedKey, sender: data.sender});
    }
});

socket.on("safe-incoming", async (username, message) => {
    const { cipherText, iv, hmac } = message;
    const symKey = await getSymmetricKey(room_id);
    const hmacKey = await getHMACKey(room_id);

    if (!symKey || !hmacKey) {
        console.error("Keys are not available to decrypt or verify the message.");
        return;
    }

    if (await verifyHMAC(cipherText + iv, hmac, hmacKey)) {
        const decryptedMessage = await decryptMessage(cipherText, new Uint8Array(iv), symKey);
        add_message(`${username}: ${decryptedMessage}`, "black");
    } else {
        console.error("HMAC verification failed. Message integrity compromised.");
    }
});