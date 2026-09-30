document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("[data-preview-form]");
    const card = document.querySelector("[data-preview-card]");
    if (!form || !card) return;

    function fieldValue(name) {
        const field = form.elements[name];
        if (!field) return "";

        // Dropdowns show the label "Part-Time" instead of part-time
        if (field.tagName === "SELECT") {
            return field.value ? field.options[field.selectedIndex].text : "";
        }
        return field.value.trim();
    }

    function formatDate(value) {
        if (!value) return "";
        const date = new Date(value + "T00:00");
        return date.toLocaleDateString("en-US", {
            year: "numeric", month: "short", day: "numeric",
        });
    }

    // Only allow real web links, never "javascript:" URLs
    function isSafeUrl(url) {
        return /^https?:\/\//i.test(url);
    }

    function updatePreview() {
        card.querySelectorAll("[data-preview]").forEach((el) => {
            let value = fieldValue(el.dataset.preview);
            if (el.dataset.format === "date") {
                value = formatDate(value);
            }
            el.textContent = value || el.dataset.placeholder || "";
        });

        card.querySelectorAll("[data-preview-status]").forEach((el) => {
            const ended = fieldValue(el.dataset.previewStatus);
            el.textContent = ended ? "Completed" : "Ongoing";
        });

        card.querySelectorAll("[data-preview-src]").forEach((el) => {
            const url = fieldValue(el.dataset.previewSrc);
            const show = isSafeUrl(url);
            el.hidden = !show;
            if (show) el.src = url;
        });

        card.querySelectorAll("[data-preview-link]").forEach((el) => {
            const url = fieldValue(el.dataset.previewLink);
            const show = isSafeUrl(url);
            el.hidden = !show;
            el.querySelector("a").href = show ? url : "#";
        });
    }

    form.addEventListener("input", updatePreview);
    form.addEventListener("change", updatePreview);
    // "reset" fires before the fields are cleared, so wait a tick before re-reading them
    form.addEventListener("reset", () => setTimeout(updatePreview));
    updatePreview();
});