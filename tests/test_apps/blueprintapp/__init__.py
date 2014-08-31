from flask import Flask

app = Flask(__name__)
app.config['DEBUG'] = True
from blueprintapp.apps.admin import admin
from blueprintapp.apps.frontend import frontend
app.register_blueprint(admin)
app.register_blueprint(frontend)
