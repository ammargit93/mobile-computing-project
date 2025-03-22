from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
API_KEY = "AIzaSyBUd2d1aAaYBSsQpLy48SMszol90MmLlVk"

@app.route("/send_otp", methods=["POST"])
def send_otp():
    phone_number = request.json.get("phone_number")
    print(phone_number)
    if not phone_number:
        return jsonify({"error": "Phone number is required"}), 400

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendVerificationCode?key={API_KEY}"
    data = {"phoneNumber": phone_number}

    response = requests.post(url, json=data)
    result = response.json()
    print(result)
    if "sessionInfo" in result:
        return jsonify({"session_info": result["sessionInfo"]})  # Return session info for verification
    else:
        return jsonify({"error": "Failed to send OTP", "details": result}), 400

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    session_info = request.json.get("session_info")
    otp_code = request.json.get("otp_code")

    if not session_info or not otp_code:
        return jsonify({"error": "Session info and OTP code are required"}), 400

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPhoneNumber?key={API_KEY}"
    data = {"sessionInfo": session_info, "code": otp_code}

    response = requests.post(url, json=data)
    result = response.json()

    if "idToken" in result:
        return jsonify({"success": True, "idToken": result["idToken"]})  # Successfully verified
    else:
        return jsonify({"error": "OTP verification failed", "details": result}), 400

if __name__ == "__main__":
    app.run(debug=True)
