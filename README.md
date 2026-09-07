Nama : Muhamad Idris Kamal

NPM : 2506637073

Kelas : PBP KKI

## Assignment 1

### 1. Semantic HTML

Yes, it really helped me. For example, semantic elements like `<section>` give the page more structure and make it easier to navigate when editing the code, and more readable too. Each `<section>` also has an `id` (like `id="skills"`) that connects to the nav link `href="#skills"`, so one-page navigation came for free. I also learned new things like using `<ul>`/`<li>` for repeated items in HTML.

### 2. Responsive Design

For me the main challenge was making it look good on mobile — how to fit things. For the skills section I used `grid-template-columns: repeat(auto-fill, ...)`, which basically divides the screen width by the card size and fits as many cards as possible, so it adapts to any screen size automatically.

### 3. Limitations and Next Steps

I think the main limitation right now is that all my content is hardcoded. If I want to add or change a skill, I have to manually edit the HTML (and sometimes the CSS), then commit and redeploy to PWS just for one small change. Based on that, the dynamic functionality I most want to add next is storing my skills (and later, projects) as data, then rendering them in the template with a loop.

### AI Usage Disclosure
In building this project, i used Claude as a learning aid. Specifically:
I asked it to explain concepts i didn't understand (in example like CSS Grid, `position: absolute`, `@keyframes`, animations, `@font-face`) rather than to write code for me. 

When I hit bugs, i described the problem and it helped me diagnose the cause (e.g. mismatched class names, fonts wont load), but I applied the fixes myself.