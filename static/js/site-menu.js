(function () {
    const toggle = document.querySelector(".site-menu-toggle");
    const menu = document.getElementById("site-menu");
    if (!toggle || !menu) return;

    function setOpen(open, focusToggle = false) {
        menu.classList.toggle("is-open", open);
        toggle.setAttribute("aria-expanded", String(open));
        if (!open && focusToggle) toggle.focus();
    }

    toggle.addEventListener("click", () => setOpen(toggle.getAttribute("aria-expanded") !== "true"));

    menu.addEventListener("click", (event) => {
        if (event.target.closest("a")) setOpen(false);
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && menu.classList.contains("is-open")) setOpen(false, true);
    });

    document.addEventListener("click", (event) => {
        if (!menu.classList.contains("is-open")) return;
        if (!menu.contains(event.target) && !toggle.contains(event.target)) setOpen(false);
    });

    window.matchMedia("(min-width: 801px)").addEventListener("change", (event) => {
        if (event.matches) setOpen(false);
    });
})();
