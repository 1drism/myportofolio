document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".education-form");
    if (!form) return;

    const placeholders = {
        institution: "Institution",
        faculty_or_major: "Faculty / Major",
        degree: "Degree",
        description: "",
    };

    function formatDate(value) {
        if (!value) return "";
        const date = new Date(value + "T00:00");
        return date.toLocaleDateString("en-US", {
            year: "numeric", month: "short", day: "numeric",
        });
    }

    function preview(name) {
        return document.querySelector(`[data-preview="${name}"]`);
    }

    function updatePreview() {
        for (const name in placeholders) {
            const value = form.elements[name].value.trim();
            preview(name).textContent = value || placeholders[name];
        }

        const start = form.elements["started_at"].value;
        const end = form.elements["ended_at"].value;

        preview("started_at").textContent = formatDate(start);
        preview("status").textContent = end ? "Completed" : "Ongoing";
    }

    form.addEventListener("input", updatePreview);
    updatePreview();
});