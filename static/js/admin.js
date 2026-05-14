/*
 * admin.js — moderator dashboard logic.
 *
 * Loads flagged messages and the user list, lets the admin delete
 * messages, block/mute users, and updates the stats. Subscribes to
 * Socket.IO `new_flag` events so the dashboard updates in real time.
 */

if (!requireAuth()) {
    throw new Error("Not authenticated");
}

const me = getUser();
if (!me || !me.is_admin) {
    showToast("Admin access required", "error");
    setTimeout(() => (window.location.href = "/chat"), 1200);
    throw new Error("Not an admin");
}

const flaggedListEl = document.getElementById("flaggedList");
const usersListEl = document.getElementById("usersList");

// Connect to Socket.IO so we receive `new_flag` events live
const socket = io({ auth: { token: getToken() } });
socket.on("new_flag", () => {
    // A new flagged message arrived — refresh both lists + stats
    loadFlagged();
    loadStats();
});

// ---- Stats ----
async function loadStats() {
    const res = await apiFetch("/api/admin/stats");
    if (!res.ok) return;
    const s = await res.json();
    document.getElementById("statTotalUsers").textContent = s.total_users;
    document.getElementById("statOnline").textContent = s.online_users;
    document.getElementById("statMessages").textContent = s.total_messages;
    document.getElementById("statFlagged").textContent = s.flagged_messages;
    document.getElementById("statBlocked").textContent = s.blocked_users;
    document.getElementById("statMuted").textContent = s.muted_users;
}

// ---- Flagged messages ----
async function loadFlagged() {
    const res = await apiFetch("/api/admin/flagged");
    if (!res.ok) return;
    const data = await res.json();
    if (data.messages.length === 0) {
        flaggedListEl.innerHTML = '<p class="empty">No flagged messages 🎉</p>';
        return;
    }
    flaggedListEl.innerHTML = "";
    data.messages.forEach((m) => {
        const item = document.createElement("div");
        item.className = "flagged-item" + (m.is_deleted ? " deleted" : "");
        const time = new Date(m.created_at).toLocaleString();
        item.innerHTML = `
            <div class="flagged-meta">
                <span><strong>${escapeHtml(m.sender_username || "?")}</strong> → ${escapeHtml(m.recipient_username || "?")}</span>
                <span>${time}</span>
            </div>
            <div class="flagged-content">${escapeHtml(m.content)}</div>
            <div class="flag-reason">⚠️ ${escapeHtml(m.flag_reason || "Flagged")}</div>
            <div class="user-row-actions">
                ${m.is_deleted
                    ? '<span class="tag">Deleted</span>'
                    : `<button class="btn btn-danger btn-sm" data-delete="${m.id}">Delete message</button>`}
            </div>
        `;
        flaggedListEl.appendChild(item);
    });

    // Wire up delete buttons
    flaggedListEl.querySelectorAll("[data-delete]").forEach((btn) => {
        btn.addEventListener("click", async () => {
            if (!confirm("Delete this message?")) return;
            const id = btn.getAttribute("data-delete");
            const res = await apiFetch(`/api/admin/messages/${id}`, { method: "DELETE" });
            if (res.ok) {
                showToast("Message deleted");
                loadFlagged();
                loadStats();
            } else {
                showToast("Could not delete message", "error");
            }
        });
    });
}

// ---- Users list ----
async function loadUsers() {
    const res = await apiFetch("/api/admin/users");
    if (!res.ok) return;
    const data = await res.json();
    if (data.users.length === 0) {
        usersListEl.innerHTML = '<p class="empty">No users yet</p>';
        return;
    }
    usersListEl.innerHTML = "";
    data.users.forEach((u) => {
        const row = document.createElement("div");
        row.className = "user-row";
        const tags = [];
        if (u.is_admin) tags.push('<span class="tag admin">admin</span>');
        if (u.is_online) tags.push('<span class="tag" style="color:var(--success);">online</span>');
        if (u.is_blocked) tags.push('<span class="tag blocked">blocked</span>');
        if (u.is_muted) tags.push('<span class="tag muted">muted</span>');

        row.innerHTML = `
            <div class="user-avatar">${u.avatar || "🌱"}</div>
            <div class="user-meta">
                <div class="user-name">${escapeHtml(u.username)}</div>
                <div class="user-tags">${tags.join("") || '<span class="tag">user</span>'}</div>
            </div>
            <div class="user-row-actions">
                ${u.is_admin ? "" : `
                    <button class="btn btn-ghost btn-sm" data-mute="${u.id}">${u.is_muted ? "Unmute" : "Mute"}</button>
                    <button class="btn btn-danger btn-sm" data-block="${u.id}">${u.is_blocked ? "Unblock" : "Block"}</button>
                `}
            </div>
        `;
        usersListEl.appendChild(row);
    });

    usersListEl.querySelectorAll("[data-block]").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const id = btn.getAttribute("data-block");
            const res = await apiFetch(`/api/admin/users/${id}/block`, { method: "POST" });
            if (res.ok) { loadUsers(); loadStats(); }
            else showToast("Action failed", "error");
        });
    });
    usersListEl.querySelectorAll("[data-mute]").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const id = btn.getAttribute("data-mute");
            const res = await apiFetch(`/api/admin/users/${id}/mute`, { method: "POST" });
            if (res.ok) { loadUsers(); loadStats(); }
            else showToast("Action failed", "error");
        });
    });
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
}

// Initial load + refresh every 10s as a safety net
loadStats();
loadFlagged();
loadUsers();
setInterval(() => {
    loadStats();
    loadUsers();
}, 10000);
