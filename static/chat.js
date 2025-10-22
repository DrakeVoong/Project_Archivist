async function saveEditMessage(event) {
    const textEntryDiv = event.currentTarget;
    const inputText = textEntryDiv.value;
    const text_address = textEntryDiv.dataset.address;

    // Change the text input back into regular text div
    const messageBox = textEntryDiv.closest(".chat-message-box");
    const messageBoxClass = Array.from(messageBox.classList).find(
        cls => cls.endsWith('-message-box') && cls !== 'chat-message-box');

    const messageRole = messageBoxClass?.split("-")[0];

    // Create the uneditable text message
    const messageTextDiv = document.createElement("div");
    messageTextDiv.classList.add("chat-message");
    messageTextDiv.classList.add(`${messageRole}-message`);
    messageTextDiv.textContent = inputText;
    
    messageBox.replaceChild(messageTextDiv, textEntryDiv);

    // Remove irrelavent messages due to message change 
    // TODO: Add a way to switch to past unedited message
    const messagesDiv = document.getElementById("chat-messages")
    while (messagesDiv.children.length > text_address.length) {
        messagesDiv.removeChild(messagesDiv.lastChild);
    }

    // Add assistant div to the chat
    const assistantMessageDiv = await createMessageDiv("assistant", "");
    const assistantTextDiv = assistantMessageDiv.querySelector(".chat-message");
    messagesDiv.appendChild(assistantMessageDiv);

    const response = await fetch("/save_edit_stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText, "address": text_address})
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
            break;
        case "message":
            // append partial text while streaming
            assistantTextDiv.textContent += obj.value;
            parent.scrollTop = parent.scrollHeight;
            break;
        case "final":
            // final chunk may be HTML/markdown already converted server-side
            assistantTextDiv.innerHTML = obj.value;
            break;
        case "assistant_address":
            assistantMessageDiv.dataset.address = obj.value;
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

function editMessage(event) {
    const clicked = event.currentTarget;

    // Change the text div into a text input div for user to edit message
    const messageBox = clicked.closest(".chat-message-box");
    const messageAddress = messageBox.dataset.address;

    const messageBoxClass = Array.from(messageBox.classList).find(
        cls => cls.endsWith('-message-box') && cls !== 'chat-message-box');
    
    // Whether it is a "user" or "assistant" message
    const messageRole = messageBoxClass?.split("-")[0];
    const messageTextDiv = messageBox.querySelector(`:scope > .${messageRole}-message`);
    const messageText = messageTextDiv.textContent;
    messageTextDiv.textContent = "";
    
    // Create editable text message
    const textBoxEntry = document.createElement("input");
    textBoxEntry.classList.add(`${messageRole}-message`);
    textBoxEntry.dataset.address = messageAddress;
    textBoxEntry.type = "text";
    textBoxEntry.value = messageText;

    textBoxEntry.addEventListener("keyup", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        saveEditMessage(event);
    }
    });

    messageBox.replaceChild(textBoxEntry, messageTextDiv);
}

// Convert an SVG file into an svg element
async function loadSVGFile(url, className) {
    const response = await fetch(url);

    const svgText = await response.text();

    const parser = new DOMParser();
    const doc = parser.parseFromString(svgText, "image/svg+xml");
    const svg = doc.documentElement;

    svg.classList.add(className);

    return svg;
}

async function createMessageDiv(role, text){
    role = role.toLowerCase();
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("chat-message-box")
    messageDiv.classList.add(role + "-message-box")
    
    // Holds the text and role of the message
    const textDiv = document.createElement("div");
    textDiv.classList.add("chat-message");
    textDiv.classList.add(role + "-message")
    textDiv.textContent = text;
    messageDiv.appendChild(textDiv);

    
    const buttonsDiv = document.createElement("div");
    buttonsDiv.classList.add("message-box-btn");
    
    if (role == "user"){
        buttonsDiv.classList.add("user-msg-box-btn");

        // Allows the user to edit the message after sending
        const editDiv = document.createElement("button");
        editDiv.classList.add("message-btn");
        editDiv.classList.add("edit-msg-btn");
        // editDiv.innerHTML = '<img class="messsage-svg" src="/static/svg/edit.svg" alt="Edit">';
        const editSVG = await loadSVGFile("/static/svg/edit.svg", "message-svg");
        editDiv.appendChild(editSVG);
        editDiv.addEventListener('click', editMessage);
        buttonsDiv.appendChild(editDiv);
        
        // Allows the user to save text to clipboard
        const copyDiv = document.createElement("button");
        copyDiv.classList.add("message-btn");
        copyDiv.classList.add("copy-msg-btn");
        // copyDiv.innerHTML = '<img class="messsage-svg" src="/static/svg/copy.svg" alt="Edit">';
        const copySVG = await loadSVGFile("/static/svg/copy.svg", "message-svg");
        copyDiv.appendChild(copySVG);
        buttonsDiv.appendChild(copyDiv);

    } else if (role == "assistant") {
        buttonsDiv.classList.add("assistant-msg-box-btn");

        // Allows the user regenerate an LLM response
        const retryDiv = document.createElement("button");
        retryDiv.classList.add("message-btn");
        retryDiv.classList.add("retry-msg-btn");
        // retryDiv.innerHTML = '<img class="messsage-svg" src="/static/svg/refresh.svg" alt="Edit">';
        const retrySVG = await loadSVGFile("/static/svg/refresh.svg", "message-svg");
        retryDiv.appendChild(retrySVG);
        buttonsDiv.appendChild(retryDiv);
    }

    messageDiv.appendChild(buttonsDiv);

    return messageDiv
}

async function receiveMessage() {
    const inputText = document.getElementById("chat-input").value;
    if (!inputText) return;

    inputText.value = "";

    const parent = document.getElementById("chat-messages");
    const userMessageDiv = await createMessageDiv("user", inputText);
    parent.appendChild(userMessageDiv);

    // Add assistant div to the chat
    const assistantMessageDiv = await createMessageDiv("assistant", "");
    const assistantTextDiv = assistantMessageDiv.querySelector(".chat-message");
    parent.appendChild(assistantMessageDiv);

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
            assistantTextDiv.textContent += obj.value;
            break;
        case "final":
            // final chunk may be HTML/markdown already converted server-side
            assistantTextDiv.innerHTML = obj.value;
            break;
        case "assistant_address":
            assistantMessageDiv.dataset.address = obj.value;
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
    chatList.innerHTML = "";
    for (const message of data) {
        const chat = document.createElement("div");
        chat.classList.add("chat-list-section");
        chat.id = message.id;
        chat.textContent = message.id; // Placeholder for now
        chat.role = "button";

        chat.addEventListener("click", () => {
            loadChat(chat.id);
        });

        chatList.appendChild(chat);
    }
}

window.addEventListener("load", () => {
    loadChatList();
});

async function loadChat(chatId) {
    const response = await fetch(`/load_chat/${chatId}`);

    const chat_message = document.getElementById("chat-messages");
    chat_message.innerHTML = "";
    
    // helper function to recursively read json
    // message tree
    async function loadChat_helper(curr, level){
        const messageDiv = await createMessageDiv(curr.role, curr.text);
        
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