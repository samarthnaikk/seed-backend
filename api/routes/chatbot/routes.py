from flask import Blueprint, request, jsonify
from flask_cors import CORS, cross_origin
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')
CORS(chatbot_bp, resources={r"/*": {"origins": "*"}})

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@chatbot_bp.route('/', methods=['GET'])
@cross_origin()
def health():
    return jsonify({"status": "healthy"}), 200

@chatbot_bp.route('/chat', methods=['POST'])
@cross_origin()
def chat():
    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
        return jsonify({"error": "Missing 'message' in request body"}), 400
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(user_message)
        reply = response.text if hasattr(response, 'text') else str(response)
        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
