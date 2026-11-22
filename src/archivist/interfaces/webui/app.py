import json
import uuid
from flask import Flask, render_template, request, jsonify, stream_with_context, Response

from archivist.config.settings import settings

app = Flask(__name__)


# --- Page Routes ----------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat/<chat_uuid>")
def load_chat(chat_uuid):
    return render_template("index.html")

@app.route("/search")
def search_view():
    return render_template("index.html")

@app.route("/settings")
@app.route("/settings/<section>")
def settings_view(section="general"):
    return render_template("index.html")


# --- API Routes ----------------------

# --- Chat ---
@app.route("/api/chat/new", methods=["POST"])
def new_chat():
    chat_uuid = str(uuid.uuid4())
    return jsonify({"chat_uuid": chat_uuid})

@app.route("/api/chat/<chat_uuid>", methods=["GET"])
def get_chat(chat_uuid):
    return jsonify({"messages": [], "title": "New Chat", "created_at": ""})

def generate_response(prompt, sampling_parameters):
    try:
        for i in range(10):
            event = {"type": "token", "content": i}
            yield f"data: {json.dumps(event)}\n\n"

        yield f"data: {json.dumps({"type": "done"})}\n\n"

    except Exception as e:
        error_event = {"type": "error", "message":str(e)}
        yield f"data: {json.dumps(error_event)}\n\n"

@app.route("/api/chat/<chat_uuid>/message", methods=["POST"])
def send_message(chat_uuid):
    data = request.get_json()
    prompt = data.get("prompt", "")
    sampling_parameters = data.get("settings", {})

    system_instruction = sampling_parameters.get("system_instruction", "")
    temperature = sampling_parameters.get("temperature", 1.0)
    top_p = sampling_parameters.get("top_p", 0.9)
    top_k = sampling_parameters.get("top_k", 40)
    min_p = sampling_parameters.get("min_p", 0.05)

    print(sampling_parameters)

    return Response(
        stream_with_context(generate_response(prompt, sampling_parameters)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering if applicable
        },
    )

# @app.route("/api/chat/history", methods=["GET"])
# def chat_history():
#     pass

# --- Settings ---

@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify(settings.config)

@app.route("/api/settings", methods=["POST"])
def update_settings():
    data = request.get_json()
    for key, value in data.items():
        settings.edit_config(key, value)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run()