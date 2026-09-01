const API_URL = "https://lumeluxe-chatbot-6fe84.containers.snapdeploy.app";

const SESSION_STORAGE_KEY = "lumeluxe_chat_session_id";
let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
}

const widget = document.getElementById("lumeluxe-chatbot-widget");
const toggleButton = document.getElementById("lumeluxe-chat-toggle");
const closeButton = document.getElementById("lumeluxe-chat-close");
const resetButton = document.getElementById("lumeluxe-chat-reset");
const chatbot = document.getElementById("lumeluxe-chatbot");
const sendButton = document.getElementById("lumeluxe-send-button");
const input = document.getElementById("lumeluxe-message-input");
const messages = document.getElementById("lumeluxe-chat-messages");

let isOpen = false;
let isTyping = false;

function setChatOpen(open) {
    isOpen = open;
    chatbot.classList.toggle("is-open", open);
    toggleButton.classList.toggle("is-active", open);
    toggleButton.setAttribute("aria-label", open ? "Close chatbot" : "Open chatbot");
}

function addUserMessage(text) {
    const row = document.createElement("div");
    row.className = "lumeluxe-chatbot-message";

    const messageRow = document.createElement("div");
    messageRow.className = "lumeluxe-chatbot-message-row lumeluxe-chatbot-message-row-user";

    const avatar = document.createElement("div");
    avatar.className = "lumeluxe-chatbot-avatar lumeluxe-chatbot-avatar-user";
    avatar.innerHTML = `
        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M12 12.2c2.4 0 4.3-1.9 4.3-4.3S14.4 3.6 12 3.6s-4.3 1.9-4.3 4.3 1.9 4.3 4.3 4.3Zm0 2.1c-3.9 0-7.1 2.4-7.1 5.3 0 .6.5 1.1 1.1 1.1h12c.6 0 1.1-.5 1.1-1.1 0-2.9-3.2-5.3-7.1-5.3Z"/>
        </svg>
    `;

    const bubble = document.createElement("div");
    bubble.className = "lumeluxe-chatbot-bubble";
    bubble.textContent = text;

    messageRow.appendChild(avatar);
    messageRow.appendChild(bubble);
    row.appendChild(messageRow);
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
}

function addThinkingIndicator() {
    const row = document.createElement("div");
    row.className = "lumeluxe-chatbot-message";

    const messageRow = document.createElement("div");
    messageRow.className = "lumeluxe-chatbot-message-row lumeluxe-chatbot-message-row-bot";

    const avatar = document.createElement("div");
    avatar.className = "lumeluxe-chatbot-avatar lumeluxe-chatbot-avatar-bot";
    avatar.innerHTML = '<img src="lumeluxe-chatbot-logo.jpeg" alt="Bot avatar">';

    const thinking = document.createElement("div");
    thinking.className = "lumeluxe-chatbot-thinking";
    thinking.innerHTML = `
        <span class="lumeluxe-chatbot-thinking-text">Thinking</span>
        <span class="lumeluxe-chatbot-thinking-dots" aria-hidden="true">
            <span></span><span></span><span></span>
        </span>
    `;

    messageRow.appendChild(avatar);
    messageRow.appendChild(thinking);
    row.appendChild(messageRow);
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
    return row;
}

function removeThinkingIndicator() {
    const thinkingRow = messages.querySelector(".lumeluxe-chatbot-message:last-child .lumeluxe-chatbot-thinking");
    if (thinkingRow) {
        const parentMessage = thinkingRow.closest(".lumeluxe-chatbot-message");
        if (parentMessage) {
            parentMessage.remove();
        }
    }
}

function addBotMessage(text) {
    const row = document.createElement("div");
    row.className = "lumeluxe-chatbot-message";

    const messageRow = document.createElement("div");
    messageRow.className = "lumeluxe-chatbot-message-row lumeluxe-chatbot-message-row-bot";

    const avatar = document.createElement("div");
    avatar.className = "lumeluxe-chatbot-avatar lumeluxe-chatbot-avatar-bot";
    avatar.innerHTML = '<img src="lumeluxe-chatbot-logo.jpeg" alt="Bot avatar">';

    const bubble = document.createElement("div");
    bubble.className = "lumeluxe-chatbot-bubble";
    bubble.textContent = "";

    messageRow.appendChild(avatar);
    messageRow.appendChild(bubble);
    row.appendChild(messageRow);
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;

    return bubble;
}

function escapeHtml(value) {
    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function formatBotText(value) {
    const escaped = escapeHtml(value);
    const parts = escaped.split("**");
    let formatted = "";

    for (let i = 0; i < parts.length; i += 1) {
        if (i % 2 === 0) {
            formatted += parts[i];
        } else {
            formatted += `<strong>${parts[i]}</strong>`;
        }
    }

    return formatted.replace(/\*/g, "");
}

async function streamText(element, fullText) {
    element.innerHTML = formatBotText(fullText);
    messages.scrollTop = messages.scrollHeight;
}

async function sendMessage() {
    const question = input.value.trim();
    if (!question || isTyping) return;

    isTyping = true;
    addUserMessage(question);
    input.value = "";
    const thinkingRow = addThinkingIndicator();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: question, session_id: sessionId })
        });

        const data = await response.json();

        if (data.session_id && data.session_id !== sessionId) {
            sessionId = data.session_id;
            localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
        }

        if (thinkingRow) {
            thinkingRow.remove();
        }

        const bubble = addBotMessage(data.answer || "I’m ready to help.");
        await streamText(bubble, data.answer || "I’m ready to help.");
    } catch (error) {
        if (thinkingRow) {
            thinkingRow.remove();
        }
        const bubble = addBotMessage("Sorry, I couldn’t connect to the chatbot server.");
        await streamText(bubble, "Sorry, I couldn’t connect to the chatbot server.");
        console.error("Chatbot Fetch Error:", error);
    } finally {
        isTyping = false;
    }
}

async function resetConversation() {
    try {
        await fetch(`${API_URL}/chat/reset`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId })
        });
    } catch (error) {
        console.error("Reset failed:", error);
    }
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    messages.innerHTML = `
        <div class="lumeluxe-chatbot-message">
            <div class="lumeluxe-chatbot-message-row lumeluxe-chatbot-message-row-bot">
                <div class="lumeluxe-chatbot-avatar lumeluxe-chatbot-avatar-bot">
                    <img src="lumeluxe-chatbot-logo.jpeg" alt="Bot avatar">
                </div>
                <div class="lumeluxe-chatbot-bubble">Hello! How can I help you today?</div>
            </div>
        </div>
    `;
}

toggleButton.addEventListener("click", () => {
    setChatOpen(!isOpen);
});

closeButton.addEventListener("click", () => setChatOpen(false));

sendButton.addEventListener("click", sendMessage);
input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        sendMessage();
    }
});
resetButton.addEventListener("click", resetConversation);

document.addEventListener("click", (event) => {
    const clickedInsideWidget = widget.contains(event.target);
    if (isOpen && !clickedInsideWidget) {
        setChatOpen(false);
    }
});

setChatOpen(false);