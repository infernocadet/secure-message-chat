To prevent Cross-Site Scripting (XSS) attacks in your web application, you can follow these steps:

1. Sanitize Input: Use a library like bleach to sanitize user input. This will remove or escape any potentially harmful characters that could be used in a script. You're already doing this in your sanitize_input function.

2. Escape Output: When displaying user-generated content, make sure to escape it so that any HTML tags or attributes it contains are not interpreted by the browser. Jinja2, the template engine used by Flask, automatically escapes output when you use the {{ }} syntax, so you're covered on this front.

3. Use HTTPOnly Cookies: If you're storing session data in cookies, make sure to set the HttpOnly flag. This prevents scripts running in the user's browser from accessing the cookie data.

4. Content Security Policy: Implement a Content Security Policy (CSP) to restrict the sources from which scripts can be loaded. This can prevent an attacker from injecting a script that loads from an external source.

5. Use Secure and HttpOnly Flags for Cookies: This will prevent the cookie from being accessed by client-side scripts, and ensure it's only sent over HTTPS.

In your Flask app, you can set these flags like this:

```py
from flask import Flask, session

app = Flask(__name__)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
```

The more layers of security, the harder it is for an attacker to exploit your application.