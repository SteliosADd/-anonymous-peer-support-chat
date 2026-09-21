/*
 * tour.js — three-step welcome tour, shown once on a user's first visit
 * to the chat. Completion is remembered in localStorage.
 *
 * Each step can spotlight an element (raised above the dimmed backdrop)
 * and can pulse a smaller element inside it.
 */
(function () {
    var KEY = "tourDone";
    // Logged-out visitors get redirected to /login by chat.js, so skip them
    try { if (localStorage.getItem(KEY) || !localStorage.getItem("token")) return; } catch (e) { return; }

    var STEPS = [
        {
            icon: "💬",
            title: "Pick someone to talk to",
            text: "Everyone here has an anonymous name. Green dots are online now. Tap a name to open a private chat.",
            spot: ".chat-sidebar",
        },
        {
            icon: "🌿",
            title: "Go at your own pace",
            text: "You will see when they are typing and when they have read your message. If a message upsets you, the ⚑ button reports it to a moderator.",
        },
        {
            icon: "🆘",
            title: "Help is always here",
            text: "If things feel too heavy, this button opens crisis lines that answer 24/7. You can use it at any time.",
            spot: ".chat-sidebar",
            pulse: "#helpBtn",
        },
    ];

    var index = 0;
    var backdrop, card, lastSpot, lastPulse, previousFocus;

    function start() {
        previousFocus = document.activeElement;
        backdrop = document.createElement("div");
        backdrop.className = "tour-backdrop";

        card = document.createElement("div");
        card.className = "tour-card";
        card.setAttribute("role", "dialog");
        card.setAttribute("aria-modal", "true");
        card.setAttribute("aria-labelledby", "tourTitle");

        document.body.appendChild(backdrop);
        document.body.appendChild(card);
        document.addEventListener("keydown", onKey);
        render();
    }

    function render() {
        var step = STEPS[index];
        var last = index === STEPS.length - 1;

        clearSpot();
        if (step.spot) {
            lastSpot = document.querySelector(step.spot);
            if (lastSpot) lastSpot.classList.add("tour-spot");
        }
        if (step.pulse) {
            lastPulse = document.querySelector(step.pulse);
            if (lastPulse) lastPulse.classList.add("tour-pulse");
        }

        var dots = STEPS.map(function (_, i) {
            return '<span class="tour-dot' + (i === index ? " on" : "") + '"></span>';
        }).join("");

        // Step content is fixed text defined above, never user input
        card.innerHTML =
            '<div class="tour-icon" aria-hidden="true">' + step.icon + "</div>" +
            '<h2 id="tourTitle">' + step.title + "</h2>" +
            "<p>" + step.text + "</p>" +
            '<div class="tour-foot">' +
            '<div class="tour-dots" aria-label="Step ' + (index + 1) + " of " + STEPS.length + '">' + dots + "</div>" +
            '<div class="tour-actions">' +
            '<button type="button" class="btn btn-ghost" data-tour="skip">' + (last ? "Close" : "Skip") + "</button>" +
            '<button type="button" class="btn btn-primary" data-tour="next">' + (last ? "Got it" : "Next") + "</button>" +
            "</div></div>";

        card.querySelector('[data-tour="next"]').focus();
        card.onclick = function (e) {
            var action = e.target.closest("[data-tour]");
            if (!action) return;
            if (action.dataset.tour === "skip") finish();
            else next();
        };
    }

    function next() {
        if (index >= STEPS.length - 1) return finish();
        index += 1;
        render();
    }

    function clearSpot() {
        if (lastSpot) lastSpot.classList.remove("tour-spot");
        if (lastPulse) lastPulse.classList.remove("tour-pulse");
        lastSpot = lastPulse = null;
    }

    function onKey(e) {
        if (e.key === "Escape") { finish(); return; }
        if (e.key !== "Tab") return;
        // Keep keyboard focus inside the tour card
        var buttons = card.querySelectorAll("button");
        var first = buttons[0], lastBtn = buttons[buttons.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); lastBtn.focus(); }
        else if (!e.shiftKey && document.activeElement === lastBtn) { e.preventDefault(); first.focus(); }
    }

    function finish() {
        try { localStorage.setItem(KEY, "1"); } catch (e) { /* ignore */ }
        clearSpot();
        document.removeEventListener("keydown", onKey);
        backdrop.remove();
        card.remove();
        if (previousFocus && previousFocus.focus) previousFocus.focus();
    }

    // Wait for the chat to settle so the spotlight targets exist
    window.addEventListener("load", function () { setTimeout(start, 700); });
})();
