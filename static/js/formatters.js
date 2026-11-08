window.PortfolioFormat = (function () {
    function toDate(value) {
        return value ? new Date(value + "T00:00") : null;
    }

    function monthYear(date) {
        return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
    }

    function techStack(value) {
        return String(value ?? "").split(",").map((item) => item.trim()).filter(Boolean).join(" · ");
    }

    function educationPeriod(startedAt, endedAt) {
        const start = toDate(startedAt);
        const end = toDate(endedAt);
        if (end) return `Graduated ${end.getFullYear()}`;
        return start ? `${start.getFullYear()} – Present` : "Start date";
    }

    function monthRange(startedAt, endedAt) {
        const start = toDate(startedAt);
        const end = toDate(endedAt);
        if (!start) return "Start date";
        if (!end) return `${monthYear(start)} – Present`;
        if (start.getFullYear() === end.getFullYear() && start.getMonth() === end.getMonth()) return monthYear(end);
        if (start.getFullYear() === end.getFullYear()) {
            return `${start.toLocaleDateString("en-US", { month: "short" })} – ${monthYear(end)}`;
        }
        return `${monthYear(start)} – ${monthYear(end)}`;
    }

    return { techStack, educationPeriod, monthRange };
})();
