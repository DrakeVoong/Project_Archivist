// --- View system ---

// Every element that belongs to a named view.
// showView() hides all of them, then reveals only the requested set.
const VIEWS = {
    chat:   ["#chat-main", "#agent-settings"],
    search: ["#search"],
};

function showView(name) {
    Object.values(VIEWS).flat().forEach((sel) => $(sel).addClass("hidden"));
    (VIEWS[name] || []).forEach((sel) => $(sel).removeClass("hidden"));
}

// --- Page state helpers ---

function resetToHome() {
    activeChatUUID = null;
    showView("chat");
    $("#chat-container").removeClass("chat-active");
    $("#title-bar").removeClass("populated");
    $("#chat-messages").empty();
    $("#prompt-input").val("");
}

// Loads an existing chat by UUID: fetches history, renders messages, shows title.
function loadChat(uuid) {
    activeChatUUID = uuid;
    showView("chat");
    $("#chat-container").addClass("chat-active");

    API.getChat(uuid)
        .done((data) => {
            $("#chat-messages").empty();
            (data.messages || []).forEach((msg) => appendMessage(msg.role, msg.content));

            if (data.title) {
                $("#chat-title").text(data.title);
                $("#title-bar").addClass("populated");
            }

            scrollToBottom();
        })
        .fail(() => {
            console.error("Failed to load chat:", uuid);
        });
}

// Appends a single message bubble and scrolls to it.
function appendMessage(role, content) {
    const cls = role === "user" ? "user-message" : "assistant-message";
    $("#chat-messages").append($("<div>").addClass(cls).text(content));
    scrollToBottom();
}

function scrollToBottom() {
    const el = document.getElementById("chat-messages");
    el.scrollTop = el.scrollHeight;
}

// --- Page load ---

$(document).ready(function () {
    const path = window.location.pathname;
    const chatMatch = path.match(/\/chat\/([a-f0-9-]{36})/);

    if (chatMatch) {
        loadChat(chatMatch[1]);
    } else if (path === "/search") {
        showView("search");
    } else {
        resetToHome();
    }
});

// --- Browser back / forward ---

window.addEventListener("popstate", () => {
    const path = window.location.pathname;
    const chatMatch = path.match(/\/chat\/([a-f0-9-]{36})/);

    if (chatMatch) {
        loadChat(chatMatch[1]);
    } else if (path === "/search") {
        showView("search");
    } else {
        resetToHome();
    }
});

// --- Sidebar ---

document.getElementById("sidebar-left-toggle-btn").addEventListener("click", () => {
    document.getElementById("nav-left").classList.toggle("collapsed");
});

$("#btn-new-chat").on("click", function () {
    window.history.pushState({}, "", "/");
    resetToHome();
});

$("#btn-search-chat").on("click", function () {
    window.history.pushState({}, "", "/search");
    showView("search");
});

// --- API ---

const API = {
    newChat: () => $.ajax({ url: "/api/chat/new", method: "POST" }),
    getChat: (uuid) => $.ajax({ url: `/api/chat/${uuid}`, method: "GET" }),
    sendMessage: (uuid, payload) => $.ajax({
        url: `/api/chat/${uuid}/message`,
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify(payload),
    }),
    getHistory: () => $.ajax({ url: "/api/chat/history", method: "GET" }),
};

// Model Settings

function getModelSettings() {
    return {
        system_instruction: $("#system-instruct textarea").val().trim(),
        temperature: parseFloat($("#temp").val()),
        top_p: parseFloat($("#topp").val()),
        top_k: parseInt($("#topk").val()),
        min_p: parseFloat($("#minp").val()),
    };
}

// Send Message

function sendMessage(prompt) {
    appendMessage("user", prompt);
    $("#prompt-input").val("");

    API.sendMessage(activeChatUUID, { prompt, settings: getModelSettings() })
        .done((response) => appendMessage("assistant", response.response))
        .fail(() => console.error("Failed to send message to chat:", activeChatUUID));
}

// --- Send button ---

let activeChatUUID = null;

$("#prompt-btn-send").on("click", function () {
    const prompt = $("#prompt-input").val().trim();
    if (!prompt) return;

    if (activeChatUUID) {
        // Already in a conversation
        sendMessage(prompt);
    } else {
        // Home page — create a new chat first
        API.newChat()
            .done((data) => {
                activeChatUUID = data.chat_uuid;
                window.history.pushState({ chatUUID: activeChatUUID }, "", `/chat/${activeChatUUID}`);
                showView("chat");
                $("#chat-container").addClass("chat-active");
                $("#chat-messages").empty();

                sendMessage(prompt);
            })
            .fail(() => console.error("Failed to create new chat"));
    }
});