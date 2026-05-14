/*
 * chat.js — the real-time chat UI.
 *
 * Handles: loading the user list, switching conversations, sending and
 * receiving messages over Socket.IO, typing indicators, online status,
 * and the crisis-warning popup triggered by the moderation system.
 */

if (!requireAuth()) {
    throw new Error("Not authenticated");
}

const me = getUser();
let activeChatUser = null;       // The user we're currently chatting with
let allUsers = [];               // Cached user list (for search + status updates)
let typingTimeout = null;

// ---- DOM references ----
const userListEl = document.getElementById("userList");
const userSearchEl = document.getElementById("userSearch");
const chatHeaderEl = document.getElementById("chatHeader");
const messagesEl = document.getElementById("messages");
const chatFormEl = document.getElementById("chatForm");
const messageInputEl = document.getElementById("messageInput");
const typingRowEl = document.getElementById("typingRow");
const typingTextEl = document.getElementById("typingText");
const crisisModalEl = document.getElementById("crisisModal");
const closeCrisisBtn = document.getElementById("closeCrisis");

// ---- Socket.IO connection ----
// We pass the JWT in the connect handshake; the server reads it in app.py
const socket = io({ auth: { token: getToken() } });

socket.on("connect_error", (err) => {
    showToast("Connection failed: " + err.message, "error");
});

// ---- User list ----
async function loadUsers() {
    try {
        const res = await apiFetch("/api/chat/users");
        if (!res.ok) return;
        const data = await res.json();
        allUsers = data.users;
        renderUserList();
    } catch (e) {
        console.error(e);
    }
}

function renderUserList() {
    const q = userSearchEl.value.trim().toLowerCase();
    const filtered = q
        ? allUsers.filter((u) => u.username.toLowerCase().includes(q))
        : allUsers;

    userListEl.innerHTML = "";
    if (filtered.length === 0) {
        userListEl.innerHTML = '<li style="padding:20px;color:var(--text-muted);text-align:center;">No users found</li>';
        return;
    }
    filtered.forEach((u) => {
        const li = document.createElement("li");
        if (activeChatUser && activeChatUser.id === u.id) li.classList.add("active");
        li.innerHTML = `
            <div class="user-avatar">${u.avatar || "🌱"}</div>
            <div class="user-meta">
                <div class="user-name">${escapeHtml(u.username)}</div>
                <div class="user-status ${u.is_online ? "online" : ""}">${u.is_online ? "Online" : "Offline"}</div>
            </div>
            <div class="online-dot ${u.is_online ? "online" : ""}"></div>
        `;
        li.addEventListener("click", () => selectChat(u));
        userListEl.appendChild(li);
    });
}

userSearchEl.addEventListener("input", renderUserList);

// ---- Selecting a conversation ----
async function selectChat(user) {
    activeChatUser = user;
    renderUserList();

    chatHeaderEl.innerHTML = `
        <div class="user-avatar">${user.avatar || "🌱"}</div>
        <div class="user-meta">
            <div class="user-name">${escapeHtml(user.username)}</div>
            <div class="user-status ${user.is_online ? "online" : ""}">${user.is_online ? "Online" : "Offline"}</div>
        </div>
    `;
    chatFormEl.style.display = "flex";
    messagesEl.innerHTML = '<p class="empty">Loading messages…</p>';

    // Load history
    try {
        const res = await apiFetch(`/api/chat/history/${user.id}`);
        if (!res.ok) return;
        const data = await res.json();
        renderMessages(data.messages);
    } catch (e) {
        console.error(e);
    }
}

function renderMessages(messages) {
    messagesEl.innerHTML = "";
    if (messages.length === 0) {
        messagesEl.innerHTML = `<p class="empty" style="text-align:center;color:var(--text-muted);margin:auto;">
            Say hello 👋 — be kind, you might be exactly what they needed today.</p>`;
        return;
    }
    messages.forEach(appendMessage);
    scrollToBottom();
}

function appendMessage(msg) {
    const isMine = msg.sender_id === me.id;
    const row = document.createElement("div");
    row.className = "message-row " + (isMine ? "sent" : "received");

    let bubbleClasses = "message-bubble";
    if (msg.is_deleted) bubbleClasses += " deleted";
    else if (msg.is_flagged) bubbleClasses += " flagged";

    const time = new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    row.innerHTML = `
        <div>
            <div class="${bubbleClasses}">${escapeHtml(msg.content)}</div>
            <div class="message-meta">${time}</div>
        </div>
    `;
    messagesEl.appendChild(row);
}

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ---- Sending messages ----
chatFormEl.addEventListener("submit", (e) => {
    e.preventDefault();
    if (!activeChatUser) return;
    const content = messageInputEl.value.trim();
    if (!content) return;

    socket.emit("send_message", {
        recipient_id: activeChatUser.id,
        content,
    });
    messageInputEl.value = "";
    autoresizeTextarea();
    // Cancel typing indicator
    socket.emit("typing", { recipient_id: activeChatUser.id, is_typing: false });
});

// Press Enter to send, Shift+Enter for newline
messageInputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        chatFormEl.requestSubmit();
    }
});

// Typing indicator — emit "typing: true", then "typing: false" after a pause
messageInputEl.addEventListener("input", () => {
    autoresizeTextarea();
    if (!activeChatUser) return;
    socket.emit("typing", { recipient_id: activeChatUser.id, is_typing: true });
    if (typingTimeout) clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        socket.emit("typing", { recipient_id: activeChatUser.id, is_typing: false });
    }, 1200);
});

function autoresizeTextarea() {
    messageInputEl.style.height = "auto";
    messageInputEl.style.height = Math.min(messageInputEl.scrollHeight, 120) + "px";
}

// ---- Incoming socket events ----
socket.on("new_message", (msg) => {
    if (
        activeChatUser &&
        (msg.sender_id === activeChatUser.id || msg.recipient_id === activeChatUser.id)
    ) {
        appendMessage(msg);
        scrollToBottom();
    } else if (msg.recipient_id === me.id) {
        // Got a message from someone we're not currently chatting with
        const sender = allUsers.find((u) => u.id === msg.sender_id);
        showToast(`💬 New message from ${sender ? sender.username : "someone"}`);
    }
});

socket.on("typing", (data) => {
    if (!activeChatUser || data.user_id !== activeChatUser.id) return;
    if (data.is_typing) {
        typingTextEl.textContent = activeChatUser.username + " is typing";
        typingRowEl.style.display = "flex";
    } else {
        typingRowEl.style.display = "none";
    }
});

socket.on("user_status", (data) => {
    // Update online/offline status in the list
    const u = allUsers.find((x) => x.id === data.user_id);
    if (u) {
        u.is_online = data.is_online;
        renderUserList();
        if (activeChatUser && activeChatUser.id === data.user_id) {
            activeChatUser.is_online = data.is_online;
            const status = chatHeaderEl.querySelector(".user-status");
            if (status) {
                status.textContent = data.is_online ? "Online" : "Offline";
                status.className = "user-status " + (data.is_online ? "online" : "");
            }
        }
    } else if (data.is_online) {
        // A brand-new user came online — refresh the list
        loadUsers();
    }
});

socket.on("error_message", (data) => {
    showToast(data.error, "error");
});

// ---- Crisis warning popup ----
// Fired by the server when the moderation module detects crisis keywords
// in a message the user just sent.
socket.on("crisis_warning", () => {
    crisisModalEl.style.display = "grid";
});

closeCrisisBtn.addEventListener("click", () => {
    crisisModalEl.style.display = "none";
});
crisisModalEl.addEventListener("click", (e) => {
    if (e.target === crisisModalEl) crisisModalEl.style.display = "none";
});

// ---- Utils ----
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// Kick everything off
loadUsers();
