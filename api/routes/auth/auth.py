from flask import Flask, request, jsonify
import random
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import redis
import json
import os
import requests
import sys
from pathlib import Path
from supabase import create_client, Client
from flask_cors import CORS,cross_origin

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

r = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    decode_responses=True,
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PASSWORD")
)


# Use Blueprint for auth routes
from flask import Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
CORS(auth_bp, resources={r"/*": {"origins": "*"}})

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

@auth_bp.route('/', methods=['GET'])
@cross_origin()
def home():
    return jsonify({
        'status': 'ok',
        'message': 'API is running',
        'service': 'noteswriter-backend'
    }), 200

def gmail_service():
    token = os.getenv("GMAIL_TOKEN")
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
    token_uri = os.getenv("GMAIL_TOKEN_URI")
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    expiry = os.getenv("GMAIL_EXPIRY")
    scopes = ["https://www.googleapis.com/auth/gmail.send"]

    creds_info = {
        "token": token,
        "refresh_token": refresh_token,
        "token_uri": token_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": scopes
    }

    if expiry:
        creds_info["expiry"] = expiry

    creds = Credentials.from_authorized_user_info(creds_info, scopes)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("gmail", "v1", credentials=creds)

def send_otp_email(to_email, otp):
    service = gmail_service()
    subject = "NotesWriter Signup OTP Code"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{
          font-family: Arial, sans-serif;
          background-color: #f6f6f6;
          padding: 20px;
        }}
        .container {{
          max-width: 400px;
          margin: auto;
          background: #ffffff;
          padding: 20px;
          border-radius: 8px;
          text-align: center;
        }}
        .otp-box {{
          display: inline-block;
          width: 40px;
          height: 40px;
          line-height: 40px;
          margin: 5px;
          font-size: 20px;
          font-weight: bold;
          border: 1px solid #ccc;
          border-radius: 6px;
          background-color: #f9f9f9;
        }}
        .footer {{
          font-size: 12px;
          color: #888;
          margin-top: 15px;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>NotesWriter OTP</h2>
        <p>Use the OTP below to complete your signup:</p>
        <div>
          {''.join(f'<span class="otp-box">{digit}</span>' for digit in otp)}
        </div>
        <div class="footer">
          This OTP is valid for a limited time.
        </div>
      </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("related")
    msg["to"] = to_email
    msg["subject"] = subject

    html_part = MIMEText(html_body, "html")
    msg.attach(html_part)

    # Optional logo attachment (inline image support)
    try:
        with open("static/logo.png", "rb") as img:
            mime_img = MIMEImage(img.read())
            mime_img.add_header("Content-ID", "<logo.png>")
            mime_img.add_header("Content-Disposition", "inline", filename="logo.png")
            msg.attach(mime_img)
    except Exception:
        pass

    raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    message = {"raw": raw_msg}

    service.users().messages().send(
        userId="me",
        body=message
    ).execute()

@auth_bp.route('/signup', methods=['POST'])
def signup():
    if request.content_type != "application/json":
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    key = f"otp:{email}"
    existing_otp = r.get(key)

    if existing_otp:
        ttl = r.ttl(key)
        return jsonify({
            "status": "exists",
            "otpSent": False,
            "timeLeft": ttl,
            "email": email
        }), 200

    otp = f"{random.randint(0, 999999):06d}"
    r.setex(key, 900, otp)

    try:
        send_otp_email(email, otp)
    except Exception as e:
        return jsonify({"error": "Failed to send email", "details": str(e)}), 500

    return jsonify({
        "status": "ok",
        "otpSent": True,
        "email": email
    }), 200

@auth_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    if request.content_type != "application/json":
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()

    email = data.get("email")
    otp = data.get("otp")
    password = data.get("password")  # hashed password

    if not email or not otp or not password:
        return jsonify({"error": "Email, OTP and password are required"}), 400

    key = f"otp:{email}"
    stored_otp = r.get(key)

    if not stored_otp:
        return jsonify({
            "status": "not_found",
            "verified": False,
            "message": "OTP does not exist or has expired"
        }), 400

    if stored_otp != otp:
        return jsonify({
            "status": "invalid",
            "verified": False,
            "message": "Invalid OTP"
        }), 400

    r.delete(key)

    try:
        supabase.table("nw_users").insert({
            "email": email,
            "password": password
        }).execute()
    except Exception as e:
        return jsonify({
            "status": "db_error",
            "verified": True,
            "message": "OTP verified but failed to create user",
            "details": str(e)
        }), 500

    return jsonify({
        "status": "verified",
        "verified": True,
        "message": "OTP verified and user created"
    }), 200

@auth_bp.route('/signin', methods=['POST'])
def signin():
    if request.content_type != "application/json":
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")  # hashed

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        result = supabase.table("nw_users").select("password").eq("email", email).execute()

        if len(result.data) == 0:
            return jsonify({"success": False}), 200

        stored_hash = result.data[0]["password"]

        if stored_hash == password:
            return jsonify({"success": True}), 200

        return jsonify({"success": False}), 200

    except Exception as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500

@auth_bp.route('/debug/redis/<email>', methods=['GET'])
def debug_redis(email):
    try:
        redis_key = f"model_output:{email}"
        cached_output = r.get(redis_key)
        ttl = r.ttl(redis_key)
        
        if cached_output:
            return jsonify({
                "email": email,
                "redis_key": redis_key,
                "ttl_seconds": ttl,
                "data": json.loads(cached_output)
            }), 200
        else:
            return jsonify({
                "email": email,
                "redis_key": redis_key,
                "message": "No data found in Redis"
            }), 404
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)