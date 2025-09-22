from flask import Flask, Response, request, render_template
import time
import json
import os

import settings
from modules.message_manager import Conversation

app = Flask(__name__)

current_conv = Conversation()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/stream", methods=["POST"])
def stream():
    data = request.json
    text = data.get("text", "")

    def generate():
        for char in text:
            yield char
            time.sleep(0.2)
    return Response(generate(), mimetype="text/plain")

@app.route("/get_chat_list", methods=["GET"])
def get_chat_list():
    conv_list = os.listdir(settings.MEMORY_DIR)
    data = []
    for conv_id in conv_list:
        data.append({"id": conv_id[:-5]})

    return Response(json.dumps(data), mimetype="application/json")

@app.route("/load_chat/<chat_id>", methods=["GET"])
def load_chat(chat_id):
    global current_conv
    memory = os.path.join(settings.MEMORY_DIR, chat_id + ".json")
    current_conv.load(memory)

    with open(memory, "r") as file:
        json_data = json.load(file)

    return Response(json.dumps(json_data), mimetype="application/json")

@app.route("/new_chat", methods=["GET"])
def new_chat():
    global current_conv
    current_conv.save()
    current_conv = Conversation()

    return Response(json.dumps({"id": current_conv.conv_id}), mimetype="application/json")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
