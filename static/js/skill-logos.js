(function () {
    const base = document.currentScript?.dataset.base || "/static/img/skills/";
    const logos = {
        python: "python",
        java: "java",
        c: "c",
        django: "django",
        git: "git",
        figma: "figma",
        aftereffect: "after-effects",
        aftereffects: "after-effects",
        adobeaftereffect: "after-effects",
        adobeaftereffects: "after-effects",
        communication: "communication",
        teamwork: "teamwork",
        problemsolving: "problem-solving",
        adaptability: "adaptability",
    };

    window.skillLogoFor = function (name) {
        const key = String(name ?? "").toLowerCase().replace(/[\s._-]/g, "");
        return logos[key] ? `${base}${logos[key]}.svg` : null;
    };
})();
