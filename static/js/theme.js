/*
 * theme.js — light/dark toggle.
 *
 * Loaded in <head> so the saved theme is applied before the page paints
 * (no flash of the wrong theme). With no saved choice, the OS setting wins.
 */
(function () {
    var saved = null;
    try { saved = localStorage.getItem("theme"); } catch (e) { /* storage blocked */ }
    var prefersLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
    apply(saved || (prefersLight ? "light" : "dark"));

    function apply(theme) {
        document.documentElement.setAttribute("data-theme", theme);
    }

    document.addEventListener("DOMContentLoaded", function () {
        var btn = document.getElementById("themeToggle");
        if (!btn) return;
        sync();
        btn.addEventListener("click", function () {
            var next = document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
            apply(next);
            try { localStorage.setItem("theme", next); } catch (e) { /* ignore */ }
            sync();
        });
        function sync() {
            var light = document.documentElement.getAttribute("data-theme") === "light";
            btn.textContent = light ? "🌙" : "☀️";
            btn.setAttribute("aria-label", light ? "Switch to dark theme" : "Switch to light theme");
        }
    });
})();
