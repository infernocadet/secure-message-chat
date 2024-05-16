// Main functionality of generating and storing public private key pairs for user security.
// Deprecated - no longer using encryption in the project.

async function generateAndStoreKeyPair(){

    const keyPair = await window.crypto.subtle.generateKey(
        {
            name: "RSA-OAEP",
            modulusLength: 2048,
            publicExponent: new Uint8Array([1, 0, 1]),
            hash: "SHA-256"
        },
        true, // whether the key is extractable (i.e., can be taken out of the web crypto API)
        ["encrypt", "decrypt"] // key usages
    );


    // export public key in a format which can be sent to server
    const exportedPublicKey = await window.crypto.subtle.exportKey(
        "spki",
        keyPair.publicKey
    );

    // convert to base64 so it can be sent in a JSON object
    const publicKeyBase64 = btoa(String.fromCharCode(...new Uint8Array(exportedPublicKey)));

    return {publicKey: publicKeyBase64, privateKey: keyPair.privateKey};
}

async function storePrivateKeyLocally(username, privateKey){
    try {
        const key = await window.crypto.subtle.exportKey('jwk', privateKey);
        const transaction = db.transaction(["PrivateKeyStore"], "readwrite");
        const store = transaction.objectStore("PrivateKeyStore");
        store.put({id: username, key: JSON.stringify(key)});
    } catch (err){
        console.error("Error exporting or storing key:", err);
    }
}

// THIS WAS FOR TESTING NOT PART OF THE FINAL PRODUCT :D - WE DO NOT SHOW PRIVATE KEYS
function logPrivateKeyForTesting(username){
    const transaction = db.transaction(["PrivateKeyStore"], "readonly");
    const store = transaction.objectStore("PrivateKeyStore");
    const request = store.get(username);

    request.onsuccess = function() {
        if (request.result) {
            console.log("(Signup)Private key:", username, request.result.key);
        } else {
            console.log("(Signup)No private key stored")
        }
    };
}