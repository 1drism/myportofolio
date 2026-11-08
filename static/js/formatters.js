window.PortfolioFormat = (function () {
    function yearOf(value) {
        return value ? new Date(value + "T00:00").getFullYear() : "";
    }

    function techStack(value) {
        return String(value ?? "").split(",").map((item) => item.trim()).filter(Boolean).join(" · ");
    }

    function educationPeriod(startedAt, endedAt) {
        if (endedAt) return `Graduated ${yearOf(endedAt)}`;
        return startedAt ? `${yearOf(startedAt)} – Present` : "Start date";
    }

    return { techStack, educationPeriod };
})();
