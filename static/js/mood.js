/*
 * mood.js — daily mood check-in and the 7-day chart.
 *
 * The chart is plain SVG built here, so the page needs no chart library.
 */

if (!requireAuth()) {
    throw new Error("Not authenticated");
}

const MOOD_FACES = { 1: "😞", 2: "😕", 3: "😐", 4: "🙂", 5: "😄" };
const MOOD_LABELS = { 1: "very low", 2: "low", 3: "okay", 4: "good", 5: "great" };

const pickerEl = document.getElementById("moodPicker");
const statusEl = document.getElementById("moodStatus");
const chartEl = document.getElementById("moodChart");
const streakEl = document.getElementById("moodStreak");
const noteEl = document.getElementById("moodNote");

let entries = {};   // { "YYYY-MM-DD": mood }

// The user's own calendar day, not UTC
function localDay(offset = 0) {
    const d = new Date();
    d.setDate(d.getDate() + offset);
    const p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

async function loadMoods() {
    const res = await apiFetch("/api/mood");
    if (!res.ok) return;
    const data = await res.json();
    entries = {};
    data.entries.forEach((e) => { entries[e.day] = e.mood; });
    render();
}

function render() {
    const today = entries[localDay()];
    pickerEl.querySelectorAll(".mood-btn").forEach((btn) => {
        btn.classList.toggle("selected", Number(btn.dataset.mood) === today);
    });
    statusEl.textContent = today
        ? `Today you felt ${MOOD_LABELS[today]}. Tap another face to change it.`
        : "You haven't checked in today.";

    renderChart();
    renderStreak();
    renderNote();
}

pickerEl.addEventListener("click", async (e) => {
    const btn = e.target.closest(".mood-btn");
    if (!btn) return;
    const mood = Number(btn.dataset.mood);
    const res = await apiFetch("/api/mood", {
        method: "POST",
        body: JSON.stringify({ mood, day: localDay() }),
    });
    if (!res.ok) {
        showToast("Could not save your check-in", "error");
        return;
    }
    entries[localDay()] = mood;
    render();
    showToast("Saved. Thanks for checking in 💚");
});

// ---- 7-day line chart ----
function renderChart() {
    const W = 560, H = 220, padX = 36, padTop = 24, padBottom = 40;
    const days = [];
    for (let i = 6; i >= 0; i--) days.push(localDay(-i));

    const x = (i) => padX + (i * (W - padX * 2)) / 6;
    const y = (m) => padTop + ((5 - m) * (H - padTop - padBottom)) / 4;

    // Gridlines for each mood level
    let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Mood over the last 7 days">
        <defs>
            <linearGradient id="moodLine" x1="0" x2="1">
                <stop offset="0" stop-color="var(--primary)"/>
                <stop offset="1" stop-color="var(--accent)"/>
            </linearGradient>
            <linearGradient id="moodFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0" stop-color="var(--primary)" stop-opacity="0.28"/>
                <stop offset="1" stop-color="var(--primary)" stop-opacity="0"/>
            </linearGradient>
        </defs>`;
    for (let m = 1; m <= 5; m++) {
        svg += `<line x1="${padX}" x2="${W - padX}" y1="${y(m)}" y2="${y(m)}" class="grid"/>
                <text x="${padX - 10}" y="${y(m) + 5}" text-anchor="end" class="face">${MOOD_FACES[m]}</text>`;
    }

    // Line and area only across consecutive logged days, so gaps stay visible
    const points = days
        .map((d, i) => (entries[d] ? { i, m: entries[d] } : null))
        .filter(Boolean);
    let segment = [];
    const segments = [];
    days.forEach((d, i) => {
        if (entries[d]) segment.push({ i, m: entries[d] });
        else if (segment.length) { segments.push(segment); segment = []; }
    });
    if (segment.length) segments.push(segment);

    segments.forEach((seg) => {
        if (seg.length < 2) return;
        const line = seg.map((p, k) => `${k ? "L" : "M"}${x(p.i)},${y(p.m)}`).join(" ");
        const area = `${line} L${x(seg[seg.length - 1].i)},${y(1)} L${x(seg[0].i)},${y(1)} Z`;
        svg += `<path d="${area}" fill="url(#moodFill)"/>
                <path d="${line}" fill="none" stroke="url(#moodLine)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;
    });
    points.forEach((p) => {
        svg += `<circle cx="${x(p.i)}" cy="${y(p.m)}" r="6" class="dot"><title>${MOOD_LABELS[p.m]}</title></circle>`;
    });

    // Weekday labels
    days.forEach((d, i) => {
        const label = new Date(d + "T12:00:00").toLocaleDateString([], { weekday: "short" });
        svg += `<text x="${x(i)}" y="${H - 14}" text-anchor="middle" class="day${i === 6 ? " today" : ""}">${label}</text>`;
    });
    svg += "</svg>";
    chartEl.innerHTML = svg;
}

function renderStreak() {
    let streak = 0;
    // Today not logged yet? Start counting from yesterday so the streak isn't lost.
    let offset = entries[localDay()] ? 0 : -1;
    while (entries[localDay(offset)]) { streak++; offset--; }
    streakEl.textContent = streak
        ? `🔥 ${streak} day${streak === 1 ? "" : "s"} in a row`
        : "";
}

// A short, gentle line that reacts to the last few check-ins
function renderNote() {
    const recent = [0, -1, -2].map((o) => entries[localDay(o)]).filter(Boolean);
    let msg = "";
    if (recent.length >= 2 && recent.every((m) => m <= 2)) {
        msg = 'The last few days sound hard. Talking helps: <a href="/chat">start a chat</a> or try a <a href="/resources#breathe">breathing exercise</a>. If it feels like too much, the crisis lines on the <a href="/resources">resources page</a> are open 24/7.';
    } else if (recent.length && recent[0] >= 4) {
        msg = "Good to see a bright day. Notice what helped and take a little of it with you.";
    } else if (!Object.keys(entries).length) {
        msg = "Check in for a few days and your week will start to show a pattern.";
    }
    noteEl.innerHTML = msg;
    noteEl.style.display = msg ? "block" : "none";
}

loadMoods();
