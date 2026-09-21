# 🌿 Anonymous Mental Health Support Chat

A safe, anonymous, real-time peer-support chat platform built with **Flask**,
**Socket.IO**, and **JWT**. Users can talk to each other privately while
keyword-based moderation and user reports flag risky messages, and people in
crisis are pointed to professional resources.

> University project, category: **Health & Wellbeing**

---

## ✨ Features

### 🔒 Anonymous user system
- No emails, real names, or tracking — you get an auto-generated anonymous
  username (e.g. `quiet_river482`) and pick an emoji avatar.
- JWT-based authentication, bcrypt-hashed passwords.

### 💬 Real-time chat
- Private 1-to-1 messaging via Socket.IO.
- Typing indicators and live online/offline status.
- Unread badges in the sidebar, a `(n)` counter in the tab title, and a
  soft sound for new messages.
- Read receipts (`✓ Sent` → `✓✓ Seen`).
- Blocked users can't be messaged and their history is hidden.

### 🛡️ Safety tools
- **Keyword moderation** (`moderation.py`): a list of crisis phrases (e.g.
  *"suicide"*, *"hurt myself"*) and distress signals (*"depressed"*,
  *"hopeless"*, …). This is simple string matching, not machine learning.
- **Report button**: users can report any message they receive. Reports go
  into the same flagged queue as keyword hits, with a live alert for admins.
- **Crisis popup**: shown automatically when a crisis phrase is detected,
  and on demand from the always-visible "Need help right now?" button.
  Hotlines are tappable `tel:` / `sms:` links.

### 🌤️ Wellbeing tools
- **Daily mood check-in** (`/mood`): one private 1–5 entry per day, a
  7-day chart, and a streak counter. No free text is stored, and even
  admins cannot read entries.
- **Guided breathing** (`/resources`): animated 4-7-8, box, and calm
  patterns.

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
- Dark and light themes with a toggle (follows your OS by default and
  remembers your choice).
- Calming teal and amber palette, serif headings, animated aurora background.
- Fully responsive. On phones the chat is two screens: the people list, then
  the conversation with a back arrow (the phone's Back button works too).
- Glass-morphism panels and smooth animations.
- Three-step welcome tour on a user's first visit to the chat.
- Skeleton loading and friendly empty states for the people list and messages.

### ♿ Accessibility
- Keyboard: every control is reachable, the people list opens with
  Enter/Space, and a "Skip to content" link is the first Tab stop.
- One visible focus ring on all focusable elements.
- Screen readers: the conversation is a live region, the crisis popup and
  the tour are labelled dialogs, and list rows announce name, status and
  unread count.
- `prefers-reduced-motion` turns off decorative animation (message pops,
  breathing orb movement, skeleton shimmer, aurora).
- Text colours meet WCAG AA (4.5:1) in both themes.

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
SQLite file (`support_chat.db`) created on first launch — no database
server required.

You should see:

```
🌿 Anonymous Mental Health Support Chat starting on http://0.0.0.0:5000
   Database: sqlite:///support_chat.db
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
Creates database `support_chat` (utf8mb4 → emoji avatars work) and user
`support_chat` with password `support_chat_pass`. Change before deploying.

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
├── models.py           # SQLAlchemy models: User, Message, MoodEntry
├── auth.py             # /api/auth — register, login, me
├── chat.py             # /api/chat — user list (with unread counts), history
├── mood.py             # /api/mood — private daily mood check-ins
├── admin.py            # /api/admin — moderation endpoints (admin-only)
├── moderation.py       # Keyword-based risk detection
├── extensions.py       # Shared Flask extensions (rate limiter)
├── tests/              # pytest suite (auth, admin, moderation)
├── pytest.ini
├── schema.sql          # MySQL database + app-user bootstrap
├── .env.example        # Sample config file — copy to `.env`
├── requirements.txt
├── requirements-dev.txt
├── templates/          # Jinja templates (server-rendered HTML shells)
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── chat.html
│   ├── mood.html
│   ├── admin.html
│   └── resources.html
└── static/
    ├── css/style.css   # Design system (dark + light themes)
    └── js/
        ├── auth.js     # Shared auth helpers + navbar
        ├── theme.js    # Light/dark toggle
        ├── tour.js     # First-visit welcome tour
        ├── chat.js     # Real-time chat client
        ├── mood.js     # Mood check-in + SVG chart
        ├── breathe.js  # Guided breathing exercise
        └── admin.js    # Admin dashboard client
```

---

## 🔐 Privacy & ethics

This project is designed **privacy-first**:

- No emails, IP logs, or analytics are collected.
- Usernames are auto-generated by the server (never typed by the user);
  the database stores nothing that ties an account back to a real person.
- Passwords are hashed with bcrypt before being persisted.
- JWT tokens are stored client-side in `localStorage` — sessions don't
  rely on server-side state.

**This app is a peer-support platform — *not* a substitute for professional
mental-health care.** The crisis modal and resources page actively point
users to licensed professionals and certified hotlines.

---

## 🧪 Running tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests spin up the app against a throwaway SQLite file (`tests/conftest.py`)
and cover registration/login, admin access control, the moderation keyword
matcher, chat safety (reports, read receipts, blocked users), and the mood
API.

---

## ⚠️ Known limitations

- **No password recovery.** Since no email or personal info is stored by
  design, a lost password means a lost account — there's nothing to
  reset it with. This is a deliberate anonymity/recovery tradeoff.
- **Rate limiting is in-memory** (`Flask-Limiter`, see `extensions.py`) —
  it resets on every restart and doesn't share state across multiple
  processes/workers. Fine for a single dev instance; swap in a
  `storage_uri` (e.g. Redis) before running this behind more than one
  worker.
- **Not production-hardened.** `app.py` runs the Flask/Socket.IO
  *development* server (`socketio.run(...)`), which prints its own
  warning about this. For a real deployment you'd front it with a
  proper ASGI/WSGI setup (e.g. `eventlet` + a reverse proxy) instead.

---

## 🧪 Customization

- **Add new moderation keywords**: edit `CRISIS_KEYWORDS` or
  `DISTRESS_KEYWORDS` in `moderation.py`.
- **Change the look**: tweak the CSS variables at the top of
  `static/css/style.css`. The `:root` block is the dark theme and
  `[data-theme="light"]` overrides it for the light theme.
- **Use a custom database URL**: set `DATABASE_URL=mysql+pymysql://…`
  (or any other SQLAlchemy URL) in `.env` to override the MYSQL_* settings.

---

## 📝 License

Built for educational purposes. Adapt freely for your own university or
research project — but please keep the crisis resources accurate and
up to date.
