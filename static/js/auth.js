/*
 * auth.js — shared helpers used on every page.
 * Keeps track of the current user, gates protected pages, and wires up
 * the navbar (login/logout buttons, user badge, admin link).
 */

// Read the stored token + user object (set during login/register)
function getToken() {
    return localStorage.getItem("token");
}

function getUser() {
    try {
        return JSON.parse(localStorage.getItem("user") || "null");
    } catch (e) {
        return null;
    }
}

function setUser(user) {
    localStorage.setItem("user", JSON.stringify(user));
}

function clearAuth() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
}

// Authenticated fetch — attaches the JWT bearer token.
async function apiFetch(url, options = {}) {
    const token = getToken();
    const headers = Object.assign(
        { "Content-Type": "application/json" },
        options.headers || {},
        token ? { Authorization: "Bearer " + token } : {}
    );
    const res = await fetch(url, { ...options, headers });
    if (res.status === 401) {
        // Token expired or invalid — bounce to login
        clearAuth();
        if (!window.location.pathname.startsWith("/login")) {
            window.location.href = "/login";
        }
    }
    return res;
}

// Render the navbar based on auth state
function renderNav() {
    const user = getUser();
    const loginBtn = document.getElementById("loginBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const userBadge = document.getElementById("userBadge");
    const adminNav = document.getElementById("adminNav");

    if (user) {
        if (loginBtn) loginBtn.style.display = "none";
        if (logoutBtn) logoutBtn.style.display = "inline-block";
        if (userBadge) {
            userBadge.style.display = "inline-flex";
            userBadge.innerHTML = `<span>${user.avatar || "🌱"}</span><span>${user.username}</span>`;
        }
        if (adminNav && user.is_admin) adminNav.style.display = "inline-block";
    } else {
        if (loginBtn) loginBtn.style.display = "inline-block";
        if (logoutBtn) logoutBtn.style.display = "none";
        if (userBadge) userBadge.style.display = "none";
        if (adminNav) adminNav.style.display = "none";
    }
}

// Logout handler
document.addEventListener("DOMContentLoaded", () => {
    renderNav();
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            clearAuth();
            window.location.href = "/";
        });
    }
});

// Pages requiring auth — kick the user to /login if no token.
function requireAuth() {
    if (!getToken()) {
        window.location.href = "/login";
        return false;
    }
    return true;
}

// A simple toast notification
function showToast(message, type = "info", timeout = 3500) {
    const t = document.createElement("div");
    t.className = "toast" + (type === "error" ? " error" : "");
    t.textContent = message;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), timeout);
}
