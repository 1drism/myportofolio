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

## Assignment 2

### 1. The request flow
So first the user types the url in the browser which sends a request to the server. Project urls.py acts as the main gateway, this file receive the url, match the base route, and forwards the rest of the url to the application urls.py. App urls.py then looks for a specific url pattern match and calls the assigned view function for example in this assignment is show_education, after that VIEW views.py acts as the controller/middleman. The view processes the request or queies of specific data through model. Model models.py represent the database structure. It retreives the requested data directly from the data base Like Education.objects.all() and returns it to the view. Last one Template template.html the view takes the data obtained from the model and passes it to the template as context. The template merges the dynamic data with the HTML skeleton using {}.

The final step is Django sending the rendered HTML back to the browser as a response.

### 2. Why use models instead of hardcoding
What if you need to add 10 more experience? With a model vs hardcoded HTML, which is easier? Adding, editing, or deleting experiences or projects can be done through the Django Admin interface without ever opening and modifying HTML files. This prevents the risk of accidentally breaking the UI structure when you simply want to update a line of text. Also having 10 projects means you must write 10 repetitive blocks of HTML. With a model, the template only needs a single HTML block wrapped in a loop.

### 3. makemigrations vs migrate:
makemigrations: Creates the blueprint or instructions. This command checks the code in models.py and creates a new migration file that records any changes.

migrate: Acts as the executor. This command reads those migration instruction files and actually applies them to the database.

Example usage for example, if I add a new field gpa = models.FloatField(default=0.0) to the Education model, I need to run makemigrations first to generate the migration file that records this change, then migrate to actually add the gpa column to the database table.

### AI Usage Disclosure
For this specific assignment i only use gemini to explain me better how the concept works like model,view,template also it helps me pointing out bugs in your test code (wrong URL names).