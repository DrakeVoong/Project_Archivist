import uuid
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


# --- Page Routes ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat/<chat_uuid>")
def load_chat(chat_uuid):
    return render_template("index.html")

@app.route("/search")
def search_view():
    return render_template("index.html")


# --- API Routes ---

@app.route("/api/chat/new", methods=["POST"])
def new_chat():
    chat_uuid = str(uuid.uuid4())
    return jsonify({"chat_uuid": chat_uuid})

@app.route("/api/chat/<chat_uuid>", methods=["GET"])
def get_chat(chat_uuid):
    return jsonify({"messages": [], "title": "New Chat", "created_at": ""})

@app.route("/api/chat/<chat_uuid>/message", methods=["POST"])
def send_message(chat_uuid):
    data = request.get_json()
    prompt = data.get("prompt", "")
    settings = data.get("settings", {})

    system_instruction = settings.get("system_instruction", "")
    temperature = settings.get("temperature", 1.0)
    top_p = settings.get("top_p", 0.9)
    top_k = settings.get("top_k", 40)
    min_p = settings.get("min_p", 0.05)

    print(settings)

    # LLM call
    return jsonify({"response": f"Echo: {prompt}", "role": "assistant"})

# @app.route("/api/chat/history", methods=["GET"])
# def chat_history():
#     pass

# @app.route("/api/settings", methods=["GET", "POST"])
# def settings():
#     pass


if __name__ == "__main__":
    app.run()