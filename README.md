# 🌿 MindSpace — Anonymous Mental Health Support Chat

A safe, anonymous, real-time peer-support chat platform built with **Flask**,
**Socket.IO**, and **JWT**. Users can talk to each other privately while
AI-assisted moderation flags risky messages and points people in crisis to
professional resources.

> University project, category: **Health & Wellbeing**

---

## ✨ Features

### 🔒 Anonymous user system
- No emails, real names, or tracking — just pick a username and an emoji avatar.
- JWT-based authentication, bcrypt-hashed passwords.

### 💬 Real-time chat
- Private 1-to-1 messaging via Socket.IO.
- Typing indicators.
- Live online/offline status.
- Message timestamps.

### 🤖 AI-assisted moderation
- Keyword detection for crisis phrases (e.g. *"suicide"*, *"hurt myself"*)
  and distress signals (*"depressed"*, *"hopeless"*, …).
- Flagged messages are surfaced on the admin dashboard.
- When a crisis phrase is detected, a supportive popup with hotline numbers
  appears immediately to the sender.

### 🛡️ Admin / moderator dashboard
- Live stats (users, online, flagged, blocked, muted).
- Flagged-message queue with one-click delete.
- Block or mute any user.
- Real-time updates via Socket.IO (`new_flag` events).

### 🌱 Mental health resources page
- Crisis hotlines (988, Crisis Text Line, Samaritans, …).
- Self-help tips, stress-management exercises (4-7-8 breathing, grounding).
- Helpful links to NAMI, Mind UK, 7 Cups, and more.

### 🎨 Modern UI
- Dark mode by default, calming lavender/mint accent palette.
- Fully responsive (mobile / tablet / desktop).
- Smooth animations, glass-morphism navbar.

---

## 🧱 Tech stack

| Layer       | Tools |
|-------------|-------|
| Backend     | Flask, Flask-SocketIO, Flask-JWT-Extended, Flask-Bcrypt, SQLAlchemy |
| Real-time   | Socket.IO (server + client) |
| Database    | SQLite (zero-setup; swap to Postgres via `DATABASE_URL`) |
| Frontend    | HTML, Vanilla JS, modern CSS (no framework — beginner-friendly) |

---

## 🚀 Getting started

### 1. Clone and install
```bash
git clone <your-repo-url>
cd -anonymous-peer-support-chat
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run
```bash
python app.py
```

The app starts at **http://localhost:5000**. The SQLite database
(`mindspace.db`) is created automatically on first run, along with a default
admin account.

### 3. Default admin credentials
| Username | Password |
|----------|----------|
| `admin`  | `admin123` |

> ⚠️ **Change these immediately in production.** Edit `config.py` or set
> `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD` as environment
> variables before first launch.

### 4. Try it out
1. Open two browser windows (one normal, one private/incognito).
2. Register two users in each.
3. Start a chat from `/chat` — typing indicators and live status work
   across both windows.
4. Send a message containing `"I feel depressed"` — admin dashboard logs
   it as flagged.
5. Send a message with `"I want to hurt myself"` — a supportive crisis
   modal pops up immediately.
6. Log in as `admin` to see the moderator dashboard at `/admin`.

---

## 📂 Project structure

```
.
├── app.py              # Flask app + Socket.IO event handlers
├── config.py           # Centralized config (secrets, DB URL, JWT)
├── models.py           # SQLAlchemy models: User, Message
├── auth.py             # /api/auth — register, login, me
├── chat.py             # /api/chat — user list, message history
├── admin.py            # /api/admin — moderation endpoints (admin-only)
├── moderation.py       # Keyword-based risk detection
├── requirements.txt
├── templates/          # Jinja templates (server-rendered HTML shells)
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── chat.html
│   ├── admin.html
│   └── resources.html
└── static/
    ├── css/style.css   # Dark-mode design system
    └── js/
        ├── auth.js     # Shared auth helpers + navbar
        ├── chat.js     # Real-time chat client
        └── admin.js    # Admin dashboard client
```

---

## 🔐 Privacy & ethics

MindSpace is designed **privacy-first**:

- No emails, IP logs, or analytics are collected.
- Usernames are user-chosen; the database stores nothing that ties an
  account back to a real person.
- Passwords are hashed with bcrypt before being persisted.
- JWT tokens are stored client-side in `localStorage` — sessions don't
  rely on server-side state.

**This app is a peer-support platform — *not* a substitute for professional
mental-health care.** The crisis modal and resources page actively point
users to licensed professionals and certified hotlines.

---

## 🧪 Customization

- **Add new moderation keywords**: edit `CRISIS_KEYWORDS` or
  `DISTRESS_KEYWORDS` in `moderation.py`.
- **Change the look**: tweak the CSS variables at the top of
  `static/css/style.css` (palette, radii, shadows).
- **Swap to Postgres**: set `DATABASE_URL=postgresql://…` before running.

---

## 📝 License

Built for educational purposes. Adapt freely for your own university or
research project — but please keep the crisis resources accurate and
up to date.
