from flask import Flask, jsonify
from .routes.auth.auth import auth_bp
from .routes.chatbot.routes import chatbot_bp

app = Flask(__name__)
app.register_blueprint(auth_bp)
app.register_blueprint(chatbot_bp)

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'API is running'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)