(function () {
    const alertIconUrl = document.currentScript?.dataset.alertIcon || "/static/img/icons/alert.svg";

    function alertIcon() {
        const icon = document.createElement("img");
        icon.className = "form-error__icon";
        icon.src = alertIconUrl;
        icon.alt = "";
        return icon;
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
            const fields = field instanceof RadioNodeList ? [...field] : [field];
            fields.filter(Boolean).forEach(input => input.setAttribute("aria-invalid", "true"));
        });
    }

    document.addEventListener("toggle", event => {
        if (event.newState !== "open" || !event.target.matches?.(".modal--form")) return;
        clearFieldErrors(event.target.querySelector("form"));
    }, true);

    window.showFieldErrors = showFieldErrors;
    window.clearFieldErrors = clearFieldErrors;
})();
