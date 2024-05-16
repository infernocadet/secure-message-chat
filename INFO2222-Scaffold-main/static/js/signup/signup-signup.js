// Sign up function sending username, encrypted password and public key to server
// Deprecated - no longer using encryption in the project.

async function signup(username, password, publicKey) {
    let signupButton = document.getElementById('signupButton');
    signupButton.disabled = true; // disables button, prevents multiple submissions
    let loginURL = "{{ url_for('signup_user') }}";

    // Hash password 
    let hashedPassword = CryptoJS.SHA256(password).toString();

    console.log("Sending data:", { username, password: hashedPassword, publicKey });

    let res = await axios.post(loginURL, {
        username: username,
        password: hashedPassword,
        publicKey: publicKey
    });
    if (!isValidURL(res.data)) {
        alert(res.data);
        signupButton.disabled = false; // re-enable button is signup fails
        return;
    }
    window.open(res.data, "_self");
}
