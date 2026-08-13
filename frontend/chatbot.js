const API_URL = "http://127.0.0.1:8000";

const SESSION_STORAGE_KEY = "lumeluxe_chat_session_id";
let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
}

const toggleButton = document.getElementById("chat-toggle");
const closeButton = document.getElementById("chat-close");
const resetButton = document.getElementById("chat-reset");
const chatbot = document.getElementById("chatbot");
const sendButton = document.getElementById("send-button");
const input = document.getElementById("message-input");
const messages = document.getElementById("chat-messages");

toggleButton.addEventListener("click", () => chatbot.classList.remove("hidden"));
closeButton.addEventListener("click", () => chatbot.classList.add("hidden"));

function formatMarkdown(text) {
    let safeText = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    safeText = safeText.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    safeText = safeText.replace(/\n/g, "<br>");
    return safeText;
}

function addMessage(text, sender) {
    const message = document.createElement("div");
    message.classList.add("message", sender);
    message.innerHTML = formatMarkdown(text);
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
}

async function sendMessage() {
    const question = input.value.trim();
    if (!question) return;

    addMessage(question, "user");
    input.value = "";
    addMessage("Thinking...", "bot");

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

        const botMessages = document.querySelectorAll(".message.bot");
        const lastBotMessage = botMessages[botMessages.length - 1];
        lastBotMessage.innerHTML = formatMarkdown(data.answer);
    } catch (error) {
        const botMessages = document.querySelectorAll(".message.bot");
        const lastBotMessage = botMessages[botMessages.length - 1];
        lastBotMessage.textContent = "Sorry, I couldn't connect to the chatbot server.";
        console.error("Chatbot Fetch Error:", error);
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
    messages.innerHTML = "";
    addMessage("Hello! How can I help you today?", "bot");
}

sendButton.addEventListener("click", sendMessage);
input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
});
resetButton.addEventListener("click", resetConversation);