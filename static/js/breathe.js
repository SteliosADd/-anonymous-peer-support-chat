/*
 * breathe.js — guided breathing on the resources page.
 *
 * Each pattern is a list of phases: [label, seconds, orb scale].
 * The orb animates with a CSS transition whose length matches the phase,
 * and a 1-second timer counts the seconds down.
 */

const PATTERNS = {
    "478": {
        hint: "Inhale 4, hold 7, exhale 8. Four rounds settle your nervous system.",
        rounds: 4,
        phases: [["Breathe in", 4, 1.35], ["Hold", 7, 1.35], ["Breathe out", 8, 0.8]],
    },
    box: {
        hint: "Inhale 4, hold 4, exhale 4, hold 4. Steady and even.",
        rounds: 4,
        phases: [["Breathe in", 4, 1.35], ["Hold", 4, 1.35], ["Breathe out", 4, 0.8], ["Hold", 4, 0.8]],
    },
    calm: {
        hint: "Inhale 4, exhale 6. A long out-breath slows your heart rate.",
        rounds: 6,
        phases: [["Breathe in", 4, 1.35], ["Breathe out", 6, 0.8]],
    },
};

const orbEl = document.getElementById("breatheOrb");
const labelEl = document.getElementById("breatheLabel");
const countEl = document.getElementById("breatheCount");
const toggleEl = document.getElementById("breatheToggle");
const hintEl = document.getElementById("breatheHint");
const patternsEl = document.getElementById("breathePatterns");

let current = "478";
let running = false;
let timer = null;

patternsEl.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-pattern]");
    if (!btn) return;
    stop();
    current = btn.dataset.pattern;
    patternsEl.querySelectorAll(".chip-btn").forEach((b) => b.classList.toggle("selected", b === btn));
    hintEl.textContent = PATTERNS[current].hint;
});

toggleEl.addEventListener("click", () => (running ? stop() : start()));

function start() {
    running = true;
    toggleEl.textContent = "Stop";
    runPhase(0, 0);
}

function stop(message = "Ready?") {
    running = false;
    clearTimeout(timer);
    toggleEl.textContent = "Start";
    labelEl.textContent = message;
    countEl.textContent = "";
    orbEl.style.transition = "transform 0.8s ease";
    orbEl.style.transform = "scale(1)";
}

function runPhase(round, index) {
    if (!running) return;
    const { phases, rounds } = PATTERNS[current];
    const [label, seconds, scale] = phases[index];

    labelEl.textContent = label;
    orbEl.style.transition = `transform ${seconds}s ease-in-out`;
    orbEl.style.transform = `scale(${scale})`;

    let left = seconds;
    countEl.textContent = left;
    const tick = () => {
        if (!running) return;
        left -= 1;
        if (left > 0) {
            countEl.textContent = left;
            timer = setTimeout(tick, 1000);
            return;
        }
        const nextIndex = (index + 1) % phases.length;
        const nextRound = nextIndex === 0 ? round + 1 : round;
        if (nextRound >= rounds) {
            stop("Well done 💚");
        } else {
            runPhase(nextRound, nextIndex);
        }
    };
    timer = setTimeout(tick, 1000);
}
