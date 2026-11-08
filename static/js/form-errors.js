(function () {
    const SVG_NS = "http://www.w3.org/2000/svg";

    function alertIcon() {
        const svg = document.createElementNS(SVG_NS, "svg");
        svg.setAttribute("class", "form-error__icon");
        svg.setAttribute("viewBox", "0 0 16 16");
        svg.setAttribute("aria-hidden", "true");
        svg.setAttribute("focusable", "false");
        const path = document.createElementNS(SVG_NS, "path");
        path.setAttribute("d", "M8 5.33333V8.66667M8 11V11.3333M8 14C11.3137 14 14 11.3137 14 8C14 4.68629 11.3137 2 8 2C4.68629 2 2 4.68629 2 8C2 11.3137 4.68629 14 8 14Z");
        svg.append(path);
        return svg;
    }

    function normalizeFieldErrors(errors) {
        return Object.fromEntries(Object.entries(errors || {}).map(([name, value]) => [
            name,
            [value].flat()
                .map(item => (typeof item === "string" ? item : item?.message))
                .filter(message => typeof message === "string"),
        ]));
    }

    function clearFieldErrors(form) {
        if (!form) return;
        form.querySelectorAll("[data-errors-for]").forEach(container => container.replaceChildren());
        form.querySelectorAll('[aria-invalid="true"]').forEach(field => field.removeAttribute("aria-invalid"));
    }

    function showFieldErrors(form, errors) {
        clearFieldErrors(form);
        Object.entries(normalizeFieldErrors(errors)).forEach(([name, messages]) => {
            const container = form.querySelector(`[data-errors-for="${CSS.escape(name)}"]`);
            if (!container || messages.length === 0) return;
            messages.forEach(message => {
                const line = document.createElement("p");
                line.className = "form-error";
                line.append(alertIcon(), document.createTextNode(message));
                container.append(line);
            });
            const field = form.elements[name];
            if (field) field.setAttribute("aria-invalid", "true");
        });
    }

    document.addEventListener("toggle", event => {
        if (event.newState !== "open" || !event.target.matches?.(".modal--form")) return;
        clearFieldErrors(event.target.querySelector("form"));
    }, true);

    window.showFieldErrors = showFieldErrors;
    window.clearFieldErrors = clearFieldErrors;
})();
