// --- View system ---

const VIEWS = {
    chat:   ["#chat-main", "#agent-settings"],
    search: ["#search"],
    settings: ["#settings"],
};

function showView(name) {
    Object.values(VIEWS).flat().forEach((sel) => {
        document.querySelector(sel).classList.add("hidden");
    });
    (VIEWS[name] || []).forEach((sel) => {
        document.querySelector(sel).classList.remove("hidden");
    });
}

const SETTINGS_VIEWS = {
    general:   "#settings-general",
    analytics: "#settings-analytics",
};

function showSettingsView(name) {
    Object.values(SETTINGS_VIEWS).forEach((sel) => {
        document.querySelector(sel).classList.add("settings-hidden");
    });
    const target = SETTINGS_VIEWS[name] || SETTINGS_VIEWS["general"];
    document.querySelector(target).classList.remove("settings-hidden");
}

// --- Page state helpers ---

function resetToHome() {
    activeChatUUID = null;
    showView("chat");
    document.getElementById("chat-container").classList.remove("chat-active");
    document.getElementById("title-bar").classList.remove("populated");
    document.getElementById("chat-messages").innerHTML = "";
    document.getElementById("prompt-input").value = "";
}

// Loads an existing chat by UUID: fetches history, renders messages, shows title.
function loadChat(uuid) {
    activeChatUUID = uuid;
    showView("chat");
    document.getElementById("chat-container").classList.add("chat-active");

    API.getChat(uuid)
        .then((data) => {
            document.getElementById("chat-messages").innerHTML = "";
            (data.messages || []).forEach((msg) => appendMessage(msg.role, msg.content));

            if (data.title) {
                document.getElementById("chat-title").textContent = data.title;
                document.getElementById("title-bar").classList.add("populated");
            }

            scrollToBottom();
        })
        .catch(() => {
            console.error("Failed to load chat:", uuid);
        });
}

// Appends a single message bubble and scrolls to it.
function appendMessage(role, content) {
    const div = document.createElement("div");
    div.className = role;
    div.textContent = content;
    document.getElementById("chat-messages").appendChild(div);
    return div;
}

function scrollToBottom() {
    const el = document.getElementById("chat-messages");
    el.scrollTop = el.scrollHeight;
}

function pageView() {
    const path = window.location.pathname;
    const chatMatch = path.match(/\/chat\/([a-f0-9-]{36})/);
    const settingsMatch = path.match(/\/settings\/(\w+)/);

    if (chatMatch) {
        loadChat(chatMatch[1]);
    } else if (path === "/search") {
        showView("search");
    } else if (settingsMatch) {
        showView("settings");
        showSettingsView(settingsMatch[1]);
    } else if (path === "/settings") {
        showView("settings");
        showSettingsView("general");
    } else {
        resetToHome();
    }
}

// --- Page load ---
$(document).ready(pageView);

// --- Browser back / forward ---
window.addEventListener("popstate", pageView);

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

$("#btn-settings").on("click", function () {
    window.history.pushState({}, "", "/settings");
    showView("settings");
});

$("#btn-settings-general").on("click", function () {
    window.history.pushState({}, "", "/settings/general");
    showView("settings");
    showSettingsView("general");
});

$("#btn-settings-analytics").on("click", function () {
    window.history.pushState({}, "", "/settings/analytics");
    showView("settings");
    showSettingsView("analytics");
});

// --- API ---

const API = {
    newChat: () => fetch("/api/chat/new", { method: "POST" }).then(r => r.json()),
    getChat: (uuid) => fetch(`/api/chat/${uuid}`, { method: "GET" }).then(r => r.json()),
    sendMessage: (uuid, payload) => fetch(`/api/chat/${uuid}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    }),
    getHistory: () => fetch("/api/chat/history", { method: "GET" }).then(r => r.json()),
};

// Model Sampling Parameters

function getModelSamplingParameters() {
    return {
        system_instruction: $("#system-instruct textarea").val().trim(),
        temperature: parseFloat($("#temp").val()),
        top_p: parseFloat($("#topp").val()),
        top_k: parseInt($("#topk").val()),
        min_p: parseFloat($("#minp").val()),
    };
}

// Send Message

async function sendMessage(prompt) {
    appendMessage("user-message", prompt);
    $("#prompt-input").val("");

    const response = await API.sendMessage(activeChatUUID, { prompt, settings: getModelSamplingParameters() });

    if (!response.ok || !response.body) {
        console.error("Failed to send message to chat:", activeChatUUID);
        return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let fullText = "";
    // const messageEl = appendMessage("assistant-message", "");

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE events are separated by double newlines
        const events = buffer.split("\n\n");
        buffer = events.pop(); // last chunk may be incomplete, keep it for next read

        for (const rawEvent of events) {
            if (!rawEvent.startsWith("data: ")) continue;
            const json = JSON.parse(rawEvent.slice(6));

            if (json.type === "token") {
                fullText += json.content;
                messageEl.text(fullText);
            } else if (json.type === "done") {
                // stream finished
            } else if (json.type === "error") {
                console.error("Stream error:", json.message);
            }
        }
    }
}

// --- Send button ---

let activeChatUUID = null;

$("#prompt-btn-send").on("click", async function () {
    const prompt = $("#prompt-input").val().trim();
    if (!prompt) return;

    if (activeChatUUID) {
        sendMessage(prompt);
    } else {
        try {
            const data = await API.newChat();
            activeChatUUID = data.chat_uuid;
            window.history.pushState({ chatUUID: activeChatUUID }, "", `/chat/${activeChatUUID}`);
            showView("chat");
            $("#chat-container").addClass("chat-active");
            $("#chat-messages").empty();

            sendMessage(prompt);
        } catch (err) {
            console.error("Failed to create new chat");
        }
    }
});