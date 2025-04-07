from flask import Flask, request, jsonify
import pyotp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pymongo import MongoClient
import os
from config import users_collection
import json
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)  
email_address = os.getenv("EMAIL")
email_password = os.getenv("PASSWORD")



@app.route('/generate-otp', methods=['POST'])
def generate_otp():
    data = request.json
    phone_number = data.get('phone_number')
    
    if not phone_number:
        return jsonify({"error": "Phone number is required"}), 400    
    user = users_collection.find_one({"phone_number": phone_number})
    if not user:
        return jsonify({"error": "User not found"}), 404
    secret_key = pyotp.random_base32()
    totp = pyotp.TOTP(secret_key)
    otp = totp.now()
    email_status = send_email(
        user['email'], 
        "Your OTP Code", 
        f"Your OTP is {otp}. It will expire in 10 minutes."
    )
    if not email_status:
        return jsonify({"error": "Failed to send OTP email"}), 500
    return jsonify({
        "message": "OTP sent successfully",
        "otp": otp,
        "secret_key": secret_key
    })


@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    phone_number = data.get('phone_number')
    otp = data.get('otp')
    secret_key = data.get('secret_key')
    
    if not all([phone_number, otp, secret_key]):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Verify OTP
    totp = pyotp.TOTP(secret_key)
    if not totp.verify(otp):
        return jsonify({"error": "Invalid OTP"}), 401
    
    # Get user information
    user = users_collection.find_one({"phone_number": phone_number})
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "message": "OTP verified successfully",
        "user": {
            "id": str(user['_id']),
            "full_name": user['full_name'],
            "user_type": user['user_type']
        }
    })

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = email_address
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.sendmail(email_address, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

if __name__ == '__main__':
    app.run(host='localhost', port=5000)