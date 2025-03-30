from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import os
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

#if error update with the below file
# CHAT_FILE = "chat_history.txt"
# USER_FILE = "users.txt"

#if error user above code
# Read file paths from environment variables
CHAT_FILE = os.getenv("CHAT_FILE", "chat_history.txt")  # Default to local file if not set
USER_FILE = os.getenv("USER_FILE", "users.txt")
def ensure_user_file():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as file:
            file.write("testuser:testpassword\n")  # Default user

ensure_user_file()
# Load chat history from file
def load_chat():
    try:
        with open(CHAT_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Save chat history to file
def save_chat(chat_data):
    with open(CHAT_FILE, "w") as file:
        json.dump(chat_data, file)

# Load registered users
def get_users():
    try:
        with open(USER_FILE, "r") as file:
            users = {}
            for line in file:
                username, password = line.strip().split(":")
                users[username] = password
            return users
    except FileNotFoundError:
        return {}

# Save a new user
def save_user(username, password):
    with open(USER_FILE, "a") as file:
        file.write(f"{username}:{password}\n")

chat_history = load_chat()

@app.route("/", methods=["GET"])
def home():
    return "Chat Server Running"

@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@socketio.on("login")
def handle_login(data):
    users = get_users()
    username = data["username"]
    password = data["password"]

    if username in users:
        if users[username] == password:
            emit("login_response", {"status": "success", "message": f"Welcome back, {username}!", "chat_history": chat_history})
        else:
            emit("login_response", {"status": "error", "message": "Incorrect password!"})
    else:
        emit("login_response", {"status": "error", "message": "Username does not exist! Please check your username."})

@socketio.on("send_message")
def handle_message(data):
    global chat_history
    chat_history.append(data)  # Store message
    save_chat(chat_history)  # Save to file
    emit("receive_message", data, broadcast=True)  # Send to all users
    emit("update_chat_history", chat_history, broadcast=True)  # Sync chat history for all users

@socketio.on("fetch_chat_history")
def send_chat_history():
    emit("update_chat_history", chat_history)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

