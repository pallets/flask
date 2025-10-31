<div align="center">
  <img src="https://raw.githubusercontent.com/pallets/flask/refs/heads/stable/docs/_static/flask-name.svg" alt="Flask" height="150">
  <p><em>Flask - The Python microframework for building web applications</em></p>
</div>

# Flask

Flask is a lightweight [WSGI] web application framework designed to make getting started quick and easy, with the ability to scale up to complex applications. It began as a simple wrapper around [Werkzeug] and [Jinja], and has become one of the most popular Python web application frameworks.

Flask offers suggestions but doesn't enforce any dependencies or project layout, giving developers the freedom to choose their tools and libraries. The ecosystem includes many community-provided extensions that make adding new functionality easy.

[WSGI]: https://wsgi.readthedocs.io/
[Werkzeug]: https://werkzeug.palletsprojects.com/
[Jinja]: https://jinja.palletsprojects.com/

---

## 🚀 Quick Start

### Installation

```bash
pip install flask
```

### Your First Flask Application

Create **app.py**:

```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

if __name__ == "__main__":
    app.run(debug=True)
```

### Run the Application

```bash
# Method 1: Using flask command
flask --app app run --debug

# Method 2: Using python
python app.py
```

Visit http://localhost:5000 in your browser to see your application!

---

## 💡 Common Examples

### Basic Routing

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Home Page'

@app.route('/user/<username>')
def show_user(username):
    return f'User: {username}'

@app.route('/post/<int:post_id>')
def show_post(post_id):
    return f'Post {post_id}'

@app.route('/path/<path:subpath>')
def show_subpath(subpath):
    return f'Subpath: {subpath}'
```

---

### Working with Templates

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)
```

Create **templates/hello.html**:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Hello from Flask</title>
</head>
<body>
    {% if name %}
        <h1>Hello {{ name }}!</h1>
    {% else %}
        <h1>Hello, World!</h1>
    {% endif %}
</body>
</html>
```

---

### Handling Forms and POST Requests

```python
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Process login logic here
        return f'Welcome {username}!'
    return render_template('login.html')
```

---

### JSON API Endpoints

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/users')
def get_users():
    users = [
        {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
        {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'}
    ]
    return jsonify(users)

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    user = {'id': user_id, 'name': 'John Doe', 'email': 'john@example.com'}
    return jsonify(user)
```

---

## 🛠️ Advanced Features

### Using Blueprints for Modular Applications

```python
from flask import Flask, Blueprint

# Create a blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    return 'Login Page'

@auth_bp.route('/register')
def register():
    return 'Register Page'

# Register blueprint in main app
app = Flask(__name__)
app.register_blueprint(auth_bp, url_prefix='/auth')
```

---

### Database Integration with Flask-SQLAlchemy

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

@app.route('/users')
def list_users():
    users = User.query.all()
    return {'users': [{'username': user.username, 'email': user.email} for user in users]}
```

---

### Error Handling

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
```

---

## 🐛 Troubleshooting Common Issues

### Application Won't Start

**Error: `ModuleNotFoundError: No module named 'flask'`**

```bash
# Make sure Flask is installed
pip install flask

# Or if using virtual environment
python -m pip install flask
```

---

**Error: "Could not locate Flask application"**

```bash
# Specify the application explicitly
flask --app app.py run

# Or set FLASK_APP environment variable
export FLASK_APP=app.py
flask run
```

---

**Error: Port Already in Use**

```bash
# Use a different port
flask run --port 5001

# Or find and kill the process using the port
lsof -ti:5000 | xargs kill -9
```

---

**Debug Mode Not Working**

```python
# Enable debug mode in code
if __name__ == "__main__":
    app.run(debug=True)
```

Or via command line:

```bash
flask run --debug
```

---

**Template Not Found**

```python
# Ensure templates directory exists and is named correctly
app = Flask(__name__, template_folder='templates')
```

---

## 📚 Project Structure

A typical Flask project structure:

```
myflaskapp/
├── app.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   └── hello.html
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── instance/
    └── config.py
```

---

## 🔧 Installation Options

### Using pip (recommended)
```bash
pip install flask
```

### Using conda
```bash
conda install -c conda-forge flask
```

### From Source
```bash
git clone https://github.com/pallets/flask
cd flask
pip install -e .
```

### With Popular Extensions
```bash
pip install flask flask-sqlalchemy flask-wtf flask-login flask-mail
```

---

## 🤝 Contributing

We welcome contributions from the community! Please see our [contribution guide][contrib] for information on:

- Reporting bugs and issues
- Requesting new features
- Asking or answering questions
- Submitting pull requests
- Code style and guidelines

[contrib]: https://palletsprojects.com/contributing/

---

## 💖 Donate

The Pallets organization develops and supports Flask and the libraries it uses. To help grow the community and allow maintainers to devote more time to the projects, [please consider donating today].

[please consider donating today]: https://palletsprojects.com/donate

---

## 📖 Documentation

Complete documentation is available at [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)

---

## 🌟 Ecosystem

Popular Flask extensions:

- **Flask-SQLAlchemy** – Database integration
- **Flask-WTF** – Form handling
- **Flask-Login** – User session management
- **Flask-Mail** – Email support
- **Flask-RESTful** – Building REST APIs
- **Flask-SocketIO** – WebSocket support

---

<div align="center">
  <sub>Built with ❤️ by the <a href="https://palletsprojects.com/">Pallets</a> community</sub>
</div>
