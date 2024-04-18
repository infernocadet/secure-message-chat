To implement end-to-end encryption (E2EE) with the ability to store message history securely on the server, ensuring that even though messages are stored, they can only be decrypted by the recipient, you can use the following detailed roadmap:

1. Secure Key Management
User Key Derivation: Use the user's password to derive encryption keys, possibly using a key derivation function like PBKDF2, Argon2, or scrypt. The derived key should not be stored on the server but used to encrypt/decrypt a session-specific symmetric key on the client-side.
Session Key Handling: Generate a unique symmetric key for each session between users when the chat starts. This key can be exchanged using the public keys of each user via an algorithm like RSA or ECC (Elliptic Curve Cryptography).
2. Asymmetric Encryption for Initial Key Exchange
Key Pair Generation: Upon account creation or on a periodic basis, each user generates a pair of keys (public and private). Store only the public key on the server.
Secure Key Exchange: Use users' public keys to encrypt and exchange the symmetric session key securely when initiating a chat session.
3. Symmetric Encryption for Messaging
Encrypting Messages: Use the symmetric session key to encrypt messages before sending them to the server. Ensure the use of a secure symmetric encryption algorithm such as AES.
Decrypting Messages: When messages are retrieved, the client uses the same symmetric key to decrypt them.
4. Using HMAC for Message Integrity and Authentication
Generating MACs: Generate a HMAC for each message using part of the symmetric key or a derived key to ensure that the message has not been altered.
Verification of MACs: Upon receiving the message, compute and verify the HMAC before decrypting to ensure integrity and authenticity.
5. Secure Storage of Messages
Encryption Before Storage: Messages should be encrypted client-side before being sent to the server for storage. The server stores only encrypted messages and never has access to decryption keys.
Decryption After Retrieval: When a user accesses the chat, the encrypted messages are downloaded and decrypted client-side.
6. Secure Session Establishment
Session Initialization: When a user logs in and accesses a chat, initiate a session key exchange to securely decrypt the message history.
Session Security: Implement measures such as session timeouts and re-authentication mechanisms to ensure the security of the session keys and the session itself.
7. Security Considerations for User Password Changes
Re-encryption of Keys: If a user changes their password, ensure mechanisms are in place to re-encrypt the session keys or any other keys derived from the user's password.
8. Handling Lost Passwords
Password Recovery: Since losing a password means losing access to the derived encryption keys, consider implementing a secure password recovery process that involves re-encrypting stored data with a new key derived from the new password, possibly involving secure user verification steps.
9. Audit and Compliance
Logging and Monitoring: Ensure that all key exchanges and access to chat sessions are logged securely for audit purposes while maintaining the confidentiality of message contents.
Compliance Checks: Regularly verify compliance with relevant data protection laws and encryption standards.
10. User Interface and Experience
Clear Indicators: Provide users with clear indicators of encryption security, such as notifications when encrypted sessions are established or if encryption fails.
Ease of Use: Ensure that the encryption processes do not hinder the user experience, aiming to make security measures as transparent as possible to the user.
This roadmap provides a robust foundation for implementing end-to-end encrypted messaging in a web application, ensuring secure communication and storage of messages, with the server acting only as a secure relay and storage point without access to unencrypted message contents.

Combining Both Encryption Types
Asymmetric Encryption for Message Exchange: In your app, for example, asymmetric encryption needs to be used for exchanging messages between users. Each message or session should use a new set of ephemeral public/private keys. These keys are used for encrypting the messages sent over the network, ensuring that even if a key is compromised, only a small portion of the communication (most often a single message) is at risk.

Symmetric Encryption for Storing Messages: The symmetric key, possibly derived from the user's password or another secret, is used to encrypt message history stored on a server. This key needs to be persistent so that the user can access and decrypt their history whenever they log in.


sign up
- user A inputs name and password
- password hashed
- generate public-private key pair for user A
- store private key locally in localstorage
- send a request to app.py --> signup_user() {username: "username", password: client_hashed_password, public_key: public_key}

window 1 (normal)
> sign up User A
> logged out User A

window 2 (incognito)
> log in User A (because User A is in database)
> howeever, there is no private key stored for user A

window 1 - chrome
window 2 - safari