from flask import Flask, request, jsonify
from flask_cors import CORS
import chatbot  # Make sure chatbot.py is in the same folder

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

# --- Chat endpoint ---
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message")
    session_id = data.get("session_id", "user1")  # default session

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Get response from your chatbot.py logic
        bot_response = chatbot.get_response(user_message, session_id)
        return jsonify({"response": bot_response})
    except Exception as e:
        # Catch any errors and send them back
        return jsonify({"response": f"Error: {str(e)}"}), 500

# --- Run server ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
