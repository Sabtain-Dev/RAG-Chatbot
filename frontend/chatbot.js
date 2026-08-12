const toggleButton = document.getElementById("chat-toggle");
const closeButton = document.getElementById("chat-close");
const chatbot = document.getElementById("chatbot");
const sendButton = document.getElementById("send-button");
const input = document.getElementById("message-input");
const messages = document.getElementById("chat-messages");

toggleButton.addEventListener("click", () => chatbot.classList.remove("hidden"));
closeButton.addEventListener("click", () => chatbot.classList.add("hidden"));

// Helper function to render simple Markdown (Bold & Newlines safely)
function formatMarkdown(text) {
    let safeText = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Convert **bold** to <strong>bold</strong>
    safeText = safeText.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Convert newlines to <br>
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
        const response = await fetch("http://127.0.0.1:8000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: question })
        });

        const data = await response.json();
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

sendButton.addEventListener("click", sendMessage);
input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
});