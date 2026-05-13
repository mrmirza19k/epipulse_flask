/**
 * EpiPulse AI — Chat Widget
 * Connects to n8n webhook: https://tabrej.app.n8n.cloud/webhook/.../chat
 */

const CHAT_WEBHOOK = "https://tabrej.app.n8n.cloud/webhook/b0468a52-13b7-4dff-9a13-4ef12b0c394a/chat";


// Generate/persist a session ID so n8n can track conversation context
const SESSION_ID = (() => {
  let id = sessionStorage.getItem("epipulse_session");
  if (!id) { id = "ep_" + Math.random().toString(36).slice(2, 11); sessionStorage.setItem("epipulse_session", id); }
  return id;
})();

// ─── DOM REFS ─────────────────────────────────────────────────────────────────
const chatToggle   = document.getElementById("chat-toggle");
const chatPanel    = document.getElementById("chat-panel");
const chatClose    = document.getElementById("chat-close");
const chatMessages = document.getElementById("chat-messages");
const chatInput    = document.getElementById("chat-input");
const chatSend     = document.getElementById("chat-send");
const chatUnread   = document.getElementById("chat-unread");
const chatSuggestions = document.getElementById("chat-suggestions");

let isOpen    = false;
let isSending = false;

// ─── OPEN / CLOSE ─────────────────────────────────────────────────────────────
function openChat() {
  isOpen = true;
  chatPanel.classList.remove("hidden");
  chatUnread.classList.add("hidden");
  chatInput.focus();
  scrollToBottom();
}
function closeChat() {
  isOpen = false;
  chatPanel.classList.add("hidden");
}
chatToggle.addEventListener("click", () => isOpen ? closeChat() : openChat());
chatClose.addEventListener("click", closeChat);

// Close on outside click
document.addEventListener("click", e => {
  if (isOpen && !document.getElementById("chat-widget").contains(e.target)) closeChat();
});

// ─── SUGGESTION CHIPS ────────────────────────────────────────────────────────
chatSuggestions.querySelectorAll(".suggestion-chip").forEach(btn => {
  btn.addEventListener("click", () => {
    const msg = btn.dataset.msg;
    chatInput.value = msg;
    sendMessage();
    chatSuggestions.style.display = "none"; // hide after first use
  });
});

// ─── INPUT AUTO-RESIZE ───────────────────────────────────────────────────────
chatInput.addEventListener("input", () => {
  chatInput.style.height = "auto";
  chatInput.style.height = Math.min(chatInput.scrollHeight, 100) + "px";
});
chatInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
chatSend.addEventListener("click", sendMessage);

// ─── MESSAGE HELPERS ─────────────────────────────────────────────────────────
function timeNow() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function appendMessage(role, html) {
  const div = document.createElement("div");
  div.className = `chat-msg ${role}`;
  div.innerHTML = `<div class="chat-bubble">${html}</div><div class="chat-time">${timeNow()}</div>`;
  chatMessages.appendChild(div);
  scrollToBottom();
  return div;
}

function appendTyping() {
  const div = document.createElement("div");
  div.className = "chat-msg bot typing-indicator";
  div.innerHTML = `<div class="chat-bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>`;
  chatMessages.appendChild(div);
  scrollToBottom();
  return div;
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function formatBotText(text) {
  // Convert basic markdown-ish patterns to HTML
  return escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`(.*?)`/g, `<code style="background:rgba(0,212,255,0.1);padding:1px 5px;border-radius:4px;font-family:var(--mono);font-size:0.9em;">$1</code>`)
    .replace(/\n/g, "<br>");
}

// ─── SEND MESSAGE ─────────────────────────────────────────────────────────────
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text || isSending) return;

  isSending = true;
  chatSend.disabled = true;
  chatInput.value = "";
  chatInput.style.height = "auto";

  // Show user bubble
  appendMessage("user", escapeHtml(text));

  // Show typing indicator
  const typingEl = appendTyping();

  try {
    const res = await fetch(CHAT_WEBHOOK, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chatInput: text,
        sessionId: SESSION_ID,
        // Pass current dashboard context
        context: {
          disease:  document.getElementById("sel-disease")?.value  || "",
          district: document.getElementById("sel-district")?.value || "",
          timestamp: new Date().toISOString(),
        }
      })
    });

    typingEl.remove();

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    // n8n chat webhook can return different shapes
    const data = await res.json();
    const reply = extractReply(data);
    appendMessage("bot", formatBotText(reply));

    // Badge if panel closed
    if (!isOpen) {
      chatUnread.classList.remove("hidden");
    }

  } catch (err) {
    typingEl.remove();
    appendMessage("bot", `<span style="color:#e74c3c;">⚠️ Couldn't reach the AI assistant right now. Please try again in a moment.</span>`);
    console.error("Chat webhook error:", err);
  } finally {
    isSending = false;
    chatSend.disabled = false;
    chatInput.focus();
  }
}

// ─── EXTRACT REPLY from various n8n response shapes ──────────────────────────
function extractReply(data) {
  // n8n @n8n/n8n-nodes-langchain Chat Trigger format
  if (typeof data === "string") return data;
  if (data?.output)                return data.output;
  if (data?.text)                  return data.text;
  if (data?.message)               return data.message;
  if (data?.response)              return data.response;
  if (data?.reply)                 return data.reply;
  // firstEntryJson / array format
  if (Array.isArray(data) && data[0]) {
    const first = data[0];
    if (first?.output)  return first.output;
    if (first?.text)    return first.text;
    if (first?.message) return first.message;
    if (first?.json)    return extractReply(first.json);
    return JSON.stringify(first);
  }
  // Generic fallback
  return JSON.stringify(data);
}
