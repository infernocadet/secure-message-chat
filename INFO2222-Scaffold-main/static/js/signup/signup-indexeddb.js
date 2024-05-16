// Powers the initiation of the secure IndexedDB database holding private keys, symmetric keys and HMAC keys.
// Deprecated - no longer using encryption in the project.

let db;
    window.onload = function() {
        // open or create database
        let request = indexedDB.open("CryptoKeys", 3);

        // create schema
        request.onupgradeneeded = function(event) {
            let db = event.target.result;

            // create object store for private keys if not exist
            if (!db.objectStoreNames.contains("PrivateKeyStore")) {
                db.createObjectStore("PrivateKeyStore", {keyPath: "id"});
            }
            
            // Create an object store for symmetric keys if it doesn't already exist
            if (!db.objectStoreNames.contains("SymmetricKeys")) {
                db.createObjectStore("SymmetricKeys", { keyPath: "id" });
            }

            // Create an object store for hmac keys if it doesn't already exist
            if (!db.objectStoreNames.contains("HMACKeys")) {
                db.createObjectStore("HMACKeys", { keyPath: "id" });
            }
        };

        request.onsuccess = function(event) {
            // start a new transaction
            db = event.target.result;
            console.log("Database opened successfully");
        };

        request.onerror = function(event) {
            console.error("Database error", event.target.errorCode);
        };
    }