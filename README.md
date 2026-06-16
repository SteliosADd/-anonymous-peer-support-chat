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
| Database    | **SQLite** out-of-the-box, **MySQL** opt-in via env (PyMySQL driver) |
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

That's it. The app starts at **http://localhost:5000** using a local
SQLite file (`mindspace.db`) created on first launch — no database
server required.

You should see:

```
🌿 MindSpace starting on http://0.0.0.0:5000
   Database: sqlite:///mindspace.db
   Default admin: admin / admin123
 * Running on http://127.0.0.1:5000
```

### 3. Default admin credentials
| Username | Password |
|----------|----------|
| `admin`  | `admin123` |

> ⚠️ **Change these in production** via `DEFAULT_ADMIN_USERNAME` and
> `DEFAULT_ADMIN_PASSWORD` env variables (or a `.env` file).

### 4. Try it out
1. Open two browser windows (one normal, one private/incognito).
2. Register two users.
3. Start a chat from `/chat` — typing indicators and live status work
   across both windows.
4. Send a message containing `"I feel depressed"` — admin dashboard logs
   it as flagged.
5. Send a message with `"I want to hurt myself"` — a supportive crisis
   modal pops up immediately.
6. Log in as `admin` to see the moderator dashboard at `/admin`.

---

## 🐬 Optional: switch to MySQL

For deployment or if your assignment requires MySQL, just flip a flag.

**a.** Install MySQL (Ubuntu/Debian):
```bash
sudo apt install mysql-server && sudo service mysql start
```
…or on macOS: `brew install mysql && brew services start mysql`.

**b.** Bootstrap the database + app user (script provided):
```bash
mysql -u root -p < schema.sql
```
Creates database `mindspace` (utf8mb4 → emoji avatars work) and user
`mindspace` with password `mindspace_pass`. Change before deploying.

**c.** Enable MySQL via env variables — copy the example file:
```bash
cp .env.example .env
```
…then uncomment the `USE_MYSQL=1` line plus the `MYSQL_*` block in `.env`.

**d.** Run:
```bash
python app.py
```

Tables (`users`, `messages`) are auto-created on first launch.

---

## 📂 Project structure

```
.
├── app.py              # Flask app + Socket.IO event handlers
├── config.py           # Centralized config (env-driven; MySQL by default)
├── models.py           # SQLAlchemy models: User, Message
├── auth.py             # /api/auth — register, login, me
├── chat.py             # /api/chat — user list, message history
├── admin.py            # /api/admin — moderation endpoints (admin-only)
├── moderation.py       # Keyword-based risk detection
├── schema.sql          # MySQL database + app-user bootstrap
├── .env.example        # Sample config file — copy to `.env`
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
- **Use a custom database URL**: set `DATABASE_URL=mysql+pymysql://…`
  (or any other SQLAlchemy URL) in `.env` to override the MYSQL_* settings.

---

## 📝 License

Built for educational purposes. Adapt freely for your own university or
research project — but please keep the crisis resources accurate and
up to date.
