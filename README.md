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

### AI Usage Disclosure
I didn't use AI for this week's task, i referenced the result from Tutorial 3, then changed the structure of it to match my original education,experience,and project html.

## Assignment 4
| Role | View portfolio & API | Star / unstar | Edit data | Create / delete data |
|---|---|---|---|---|
| Visitor (not logged in) | Yes | No (redirected to login) | No (redirected to login) | No (redirected to login) |
| Regular user | Yes | Yes | No (403) | No (403) |
| Editor | Yes | Yes | Yes | No (403) |
| Portfolio owner (superuser) | Yes | Yes | Yes | Yes |

This applies to all three sections Education, Projects, and Experience. Stars are available on Education and Projects.

### How I implemented it

**Editor role**
I created a group called Editor in Django Admin and added test accounts to it from the Users page, so the role can only be assigned through admin. In views.py I made a small helper, `is_editor(user)`, which returns user.groups.filter(name='Editor').exists(). The edit views (`edit_education`, `edit_project`, `edit_experience`) let a user through if they are a superuser or an editor. The create and delete views still only allow the superuser.

**Server-side checks**
Every view that changes data uses @login_required(login_url="/login/"), so a visitor who isn't logged in gets redirected to the login page instead of seeing an error. After that, each view checks the role and raises `PermissionDenied` if the user isn't allowed, which makes Django return 403 Forbidden. I do the check on the server because hiding a button doesn't stop anyone from typing the URL or sending the POST request themselves.

**Hiding controls in templates**
`show_education`, `show_projects`, and `show_experience` pass `is_editor` into the template context. The Edit button is wrapped in {% if user.is_superuser or is_editor %}, while the Add button and the delete modal stay inside {% if user.is_superuser %}`. This way each role only sees the buttons it can actually use. This is just for the user experience; the real protection is still the server-side check.

**Star feature**
I added `starred_by = models.ManyToManyField(User, related_name="starred_education", blank=True)` to Education (and elated_name="starred_projects" on Project) and ran the migrations. The toggle_education_star and toggle_project_star views only act on POST requests, and the form includes {% csrf_token %}. If the user is already in `starred_by` they get removed, otherwise they get added. A ManyToMany relation can only store each user–item pair once, so one user can only give one star per item. The button shows the total count with `starred_by.count`, says "Star" or "Unstar" depending on whether the current user already starred it, and changes color when starred. Visitors who aren't logged in get redirected to login when they click it.

**JSON endpoint**
Once I added `starred_by`, the serializer started including it in /api/education/. By default that would be a list of raw user IDs, which exposes internal database IDs. I added use_natural_foreign_keys=True to serializers.serialize(...) so it shows usernames instead. The User model itself is never serialized, so passwords and emails never appear in the api.

### AI usage disclosure
I used Claude as a guide throughout Tutorial 4 and this assignment. It explained the concepts step by step and gave me hints for the Editor role and the Education star feature, which I then wrote and adapted myself in `views.py`, `models.py`, `urls.py`, and the templates. It also reviewed my code and caught bugs, such as my `is_editor` helper expecting a `request` while I was calling it with `request.user`. For the extra features, the `form-preview.js` live preview script claude teaches me step by step on how to write it without giving direct answer. I asked it to explain JavaScript line by line so I understood the script before using it, and I integrated it into my templates and fixed the empty preview myself once I found the missing `data-preview-form` attributes. The AI was not always right, so I verified its suggestions against my own code and the course pages.