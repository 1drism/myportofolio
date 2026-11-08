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

    function toDate(value) {
        return value ? new Date(value + "T00:00") : null;
    }

    function monthYear(date) {
        return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
    }

    function formatMonthRange(start, end) {
        if (!start) return "Start date";
        if (!end) return `${monthYear(start)} – Present`;
        if (start.getFullYear() === end.getFullYear() && start.getMonth() === end.getMonth()) return monthYear(end);
        if (start.getFullYear() === end.getFullYear()) {
            return `${start.toLocaleDateString("en-US", { month: "short" })} – ${monthYear(end)}`;
        }
        return `${monthYear(start)} – ${monthYear(end)}`;
    }

    // Only allow real web links or the site's own files, never "javascript:" URLs
    function isSafeUrl(url) {
        return /^https?:\/\//i.test(url) || /^\/(?!\/)/.test(url);
    }

    function updatePreview() {
        card.querySelectorAll("[data-preview]").forEach((el) => {
            let value = fieldValue(el.dataset.preview);
            if (el.dataset.format === "date") {
                value = formatDate(value);
            } else if (el.dataset.format === "list") {
                value = window.PortfolioFormat.techStack(value);
            }
            el.textContent = value || el.dataset.placeholder || "";
        });

        card.querySelectorAll("[data-preview-status]").forEach((el) => {
            const ended = fieldValue(el.dataset.previewStatus);
            el.textContent = ended ? "Completed" : "Ongoing";
            el.classList.toggle("is-ongoing", !ended);
        });

        card.querySelectorAll("[data-preview-range]").forEach((el) => {
            const [startName, endName] = el.dataset.previewRange.split(" ");
            el.textContent = formatMonthRange(toDate(fieldValue(startName)), toDate(fieldValue(endName)));
        });

        card.querySelectorAll("[data-preview-period]").forEach((el) => {
            const [startName, endName] = el.dataset.previewPeriod.split(" ");
            el.textContent = window.PortfolioFormat.educationPeriod(fieldValue(startName), fieldValue(endName));
        });

        card.querySelectorAll("[data-preview-src]").forEach((el) => {
            const url = fieldValue(el.dataset.previewSrc);
            const logo = el.dataset.previewLogo && window.skillLogoFor
                ? window.skillLogoFor(fieldValue(el.dataset.previewLogo))
                : null;
            const sources = [isSafeUrl(url) ? url : null, logo, el.dataset.previewDefault].filter(Boolean);
            const src = sources.shift();
            el.hidden = !src;
            el.onerror = () => {
                if (sources.length) el.src = sources.shift();
                else el.hidden = true;
            };
            if (src) el.src = src;
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