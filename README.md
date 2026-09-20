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

## Assignment 3

### 1. Why we use Django’s ModelForm
A ModelForm builds the form straight from the model, so the form structure stays in sync with the model definition. In EducationForm I only declare model = Education and list the fields, and Django generates the inputs, labels, and validation from the model itself max_length=100 on institution is enforced, and started_at is parsed into a real Python date. Building it by hand would mean writing every <input> and then pulling each value out of request.POST, checking types, and converting the date strings myself, and every model change would mean editing the template and the view too. The same form class also handles updates, edit_education passes instance=education so save() updates the row instead of inserting a new one.

The {% csrf_token %} acts like a secret handshake between my website and users to stop unwanted infiltrators from making unauthorized changes. Browsers attach cookies based on where a request is going, not where it came from, so another site could submit a form to my education/<id>/delete/ URL and the browser would send my session cookie along with it. Django puts a secret token in the form and checks it against the one tied to my session, and the same origin policy stops an attacker's page from reading it.

### 2.  Why JSON is preferred over XML
I think JSON is preferred over XML in modern web development primarily because its syntax is easier to read and its seamless integration with JavaScript which make data transfer faster and significantly easier to process. While XML is highly repetitive forcing every field name to be written twice (like <name>Idris</name> instead of "name": "Idris")—JSON keeps payloads small, which saves time and data. Furthermore, JSON maps directly onto native data structures like Python dictionaries or JavaScript objects, making parsing much faster than XML.

### 3. JSON flow, and why serialization is needed
When the browser requests /api/education/, the project urls.py hands the path to the app urls.py, which matches it and calls get_education_json. The view searches for a term, filters the database records, and converts the results into JSON using Django's serializer before sending it back as an HTTP response. Another view, show_education, reuses this exact JSON. It fetches the data, unpacks it back into actual Python objects using serializers.deserialize, and sends those objects to the template.

Serialization is necessary because a live Python object exists only in the server memory as a reference to allocated data, meaning it cannot travel over a network in its native form. Serialization converts these complex objects into a self contained text representation which translating dates into ISO strings and UUIDs into plain strings so that any client, regardless of the programming language it uses, can receive the data and parse it back into its own native structures.