from flask import Flask, request, jsonify
from flask_cors import CORS
import chatbot
import traceback

app = Flask(__name__)
CORS(app)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        user_message = data.get("message")
        session_id = data.get("session_id", "user1")  # Use frontend-provided session

        if not user_message or not isinstance(user_message, str):
            return jsonify({"error": "No valid 'message' provided"}), 400

        # Get bot response (uses chatbot.py's session tracking)
        try:
            bot_response = chatbot.get_response(user_message, session_id)
            if not bot_response:
                bot_response = "Sorry, I couldn't generate a response."
        except Exception as e:
            print("Error in chatbot.get_response:\n", traceback.format_exc())
            bot_response = f"Error generating response: {str(e)}"

        return jsonify({"response": bot_response, "session_id": session_id})

    except Exception as e:
        print("Unexpected server error:\n", traceback.format_exc())
        return jsonify({"response": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
