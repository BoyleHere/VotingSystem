import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from random import randint
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from auth import send_otp  # Assuming you have auth.py in the same directory
from vote import submit_vote  # Assuming you have vote.py in the same directory
from blockchain import Blockchain, is_chain_valid  # Assuming you have blockchain.py
from tally import tally_votes  # Assuming you have tally.py
from flask_session import Session

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management

# Database configuration using SQLite (for simplicity, you can switch to PostgreSQL or MySQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voters.db'  # Store database in 'voters.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_SQLALCHEMY"] = db
app.config["SESSION_TIMEOUT"] = 60 
Session(app)

# Blockchain initialization
blockchain = Blockchain()

# Voter Model for the database
class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    aadhar = db.Column(db.String(12), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)  # Add age to the database
    email = db.Column(db.String(120), unique=True, nullable=False)  # Add email to the database
    has_voted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Voter {self.username}>"

# Create the database tables (run this once)
with app.app_context():
    db.create_all()
# Email credentials
SENDER_EMAIL = "shreeyamo123@gmail.com"  # Replace with your email
SENDER_PASSWORD = "djog arjk vuur onyl"  # Replace with your email password or app password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


# Function to send OTP via email
def send_otp_via_email(otp, recipient_email):
    subject = "Your OTP for Voting"
    body = f"Your OTP for voting is: {otp}"

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Set up the server and login
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # Send email
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()  # Close the connection

        # Flash message to indicate successful OTP sending
        flash("OTP sent successfully to your registered email address.", "success")
    except Exception as e:
        # Flash message to indicate error in sending OTP
        flash(f"Failed to send OTP email. Error: {e}", "error")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        aadhar = request.form['aadhar']
        age = int(request.form['age'])
        email = request.form['email']

        # Validation for Aadhaar and age
        if len(aadhar) != 12:
            flash('Aadhaar number must be 12 digits long.', 'error')
            return redirect(url_for('register'))
        if age < 18:
            flash('You must be at least 18 years old to register.', 'error')
            return redirect(url_for('register'))

        # Check if username or Aadhaar already exists
        # existing_user = Voter.query.filter_by(username=username).first()
        existing_aadhar = Voter.query.filter_by(aadhar=aadhar).first()
        existing_email = Voter.query.filter_by(email=email).first()

        if existing_aadhar or existing_email:
            flash('Aadhaar, or Email already exists!', 'error')
            return redirect(url_for('register'))

        # Generate and send OTP
        otp = send_otp()
        session['aadhar'] = aadhar
        session['username'] = username
        session['otp'] = otp
        session['password'] = password  # Store password in the session
        session['age'] = age  # Store age in the session
        session['email'] = email
        send_otp_via_email(otp, email)

        # Redirect to OTP verification page
        return redirect(url_for('verify_otp', username=username))  # Pass username to verify_otp

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        voter = Voter.query.filter_by(email=email).first()
        entered_password_hash = hashlib.sha256(password.encode()).hexdigest()
        if voter and entered_password_hash == voter.password:
            session['logged_in'] = True
            session['aadhar'] = voter.aadhar
            session['email'] = voter.email  # Store email in session
            flash('Login successful!', 'success')
            return redirect(url_for('cast_vote'))
        else:
            flash('Invalid email or password!', 'error')
    return render_template('login.html')


@app.route('/cast_vote', methods=['GET', 'POST'])
def cast_vote():
    if not session.get('logged_in'):
        flash('Please log in to vote.', 'error')
        return redirect(url_for('login'))

    voter = Voter.query.filter_by(aadhar=session.get('aadhar')).first()
    if voter:
        if voter.has_voted:
            flash('You have already voted.', 'error')
            return redirect(url_for('index'))  # Redirect to index.html
        else:
            if request.method == 'POST':
                selected_party = request.form.get('party')
                if not selected_party:
                    flash('Please select a party.', 'error')
                    return redirect(url_for('cast_vote'))

                vote_data = submit_vote(selected_party)  # From vote.py
                blockchain.add_block(vote_data)
                voter.has_voted = True
                db.session.commit()
                flash('Vote cast successfully!', 'success')
                return redirect(url_for('vote_confirmation'))  # Redirect to vote_confirmation
            else:
                return render_template('vote.html')
    else:
        flash('Voter not found.', 'error')
        return redirect(url_for('index'))  # Redirect to index.html



@app.route('/verify_otp/<username>', methods=['GET', 'POST'])
def verify_otp(username):
    if request.method == 'POST':
        entered_otp = request.form['otp']
        aadhar = session.get('aadhar')
        stored_otp = session.get('otp')

        if entered_otp == stored_otp:
            # OTP is correct, add the user to the database
            password = session.get('password')  # Retrieve password from session
            age = session.get('age')  # Retrieve age from session
            email = session.get('email')  # Retrieve email from session

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            new_voter = Voter(username=username, password=hashed_password, aadhar=aadhar, age=age, email=email)
            db.session.add(new_voter)
            db.session.commit()

            flash('Registration successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Incorrect OTP.', 'error')
            return redirect(url_for('verify_otp', username=username))

    return render_template('verify_otp.html', username=username)




@app.route('/vote_confirmation')
def vote_confirmation():
    return render_template('vote_confirmation.html')


@app.route('/view_votes')
def view_votes():
    is_chain_valid(blockchain)  # Check blockchain integrity
    results = tally_votes(blockchain.chain)  # From tally.py
    return render_template('view_votes.html', results=results)  # Pass results to the template


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('aadhar', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
