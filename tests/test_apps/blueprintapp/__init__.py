from flask import Flask
from blueprintapp.apps.admin import admin
from blueprintapp.apps.frontend import frontend

app = Flask(__name__)
app.config['DEBUG'] = True
app.register_blueprint(admin)
app.register_blueprint(frontend)
