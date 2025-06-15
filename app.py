from flask import Flask, render_template
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your_app_password'      # Replace with your app password
mail = Mail(app)

# Import admin module
import admin

# Import routes after app creation
from urls import *

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
