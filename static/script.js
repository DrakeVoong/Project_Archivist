
window.addEventListener("DOMContentLoaded", () => {
  fetch("/run")
    .then(response => response.text())
    .then(data => {
      console.log("Server response:", data);
    });
});


async function receiveMessage() {
    const inputText = document.getElementById("chat-input").value;
    if (!inputText) return;

    const parent = document.getElementById("chat-messages");

    // Add user message to the chat
    const userMessageDiv = document.createElement("div");
    userMessageDiv.classList.add("chat-message");
    userMessageDiv.classList.add("user-message");
    userMessageDiv.textContent = inputText;
    parent.appendChild(userMessageDiv);

    // Add assistant div to the chat
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("chat-message"); 
    messageDiv.classList.add("assistant-message");
    parent.appendChild(messageDiv);

    // Send input to Python backend
    const response = await fetch("/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    function handleLine(line) {
        // line is a single JSON string like: {"type":"stream","value":"..."}
        let obj;
        try { obj = JSON.parse(line); }
        catch (e) { console.error("Malformed JSON line:", line); return; }

        switch (obj.type) {
        case "user_address":
            userMessageDiv.dataset.address = obj.value;
            break;
        case "message":
            // append partial text while streaming
            messageDiv.textContent += obj.value;
            break;
        case "final":
            // final chunk may be HTML/markdown already converted server-side
            messageDiv.innerHTML = obj.value;
            break;
        case "assistant_address":
            messageDiv.dataset.address = obj.value;
            break;
        default:
            console.warn("Unknown chunk type:", obj.type);
        }
    }

    while (true) {
        const { value, done } = await reader.read();
        if (value) buffer += decoder.decode(value, { stream: true });

        // extract complete lines terminated by \n
        let nl;
        while ((nl = buffer.indexOf("\n")) !== -1) {
            const line = buffer.slice(0, nl).trim();
            buffer = buffer.slice(nl + 1);
            if (line) handleLine(line);
        }

        if (done) {
            // flush decoder and any remaining buffer
            buffer += decoder.decode();
            buffer = buffer.trim();
            if (buffer) {
                // there may be one last line without trailing \n
                buffer.split("\n").forEach(l => { if (l.trim()) handleLine(l.trim()); });
            }
            break;
        }
    } 

    loadChatList();

    // Scroll to bottom if needed
    parent.scrollTop = parent.scrollHeight;
}

// Message send listeners
document.getElementById("chat-send-btn").addEventListener("click", receiveMessage);

const input = document.getElementById("chat-input");
input.addEventListener("keyup", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    receiveMessage();
  }
});

async function loadChatList() {
    const response = await fetch("/get_chat_list");
    const data = await response.json();

    const chatList = document.getElementById("chat-list");
    for (const message of data) {
        const chat = document.createElement("div");
        chat.id = message.id;
        chat.textContent = message.id; // Placeholder for now
        chat.role = "button";

        chat.addEventListener("click", () => {
            loadChat(chat.id);
        });

        chatList.appendChild(chat);
    }
}

window.onload = () => {
    loadChatList();
};

async function loadChat(chatId) {
    const response = await fetch(`/load_chat/${chatId}`);

    const chat_message = document.getElementById("chat-messages");
    chat_message.innerHTML = "";
    
    // helper function to recursively read json
    // message tree
    function loadChat_helper(curr, level){
        const messageDiv = document.createElement("div");
        messageDiv.textContent = curr.text;
        messageDiv.classList.add("chat-message");
        messageDiv.dataset.address = curr.address;
        
        if (curr.role == "User") {
            messageDiv.classList.add("user-message");
        } else if (curr.role == "Assistant") {
            messageDiv.classList.add("assistant-message");
        }
        
        chat_message.appendChild(messageDiv);
        
        if ("children" in curr) {
            for (const child of curr.children) {
                loadChat_helper(child, level + 1);
            }
        }
        
    }
    
    const data = await response.json();
    chat_message.dataset.conv_id = data.id;
    const message_list = data.messages
    // Traverse json
    for (const message of message_list) {
        loadChat_helper(message, 0);
    }
}

// New conversation
document.getElementById("new-chat-btn").addEventListener("click", async () => {
    const response = await fetch("/new_chat");

    const data = await response.json();

    const chat_list = document.getElementById("chat-messages");
    chat_list.innerHTML = "";
    chat_list.dataset.conv_id = data.id;
})