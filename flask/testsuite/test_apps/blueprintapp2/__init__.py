from flask import Flask, render_template

app = Flask(__name__)
from blueprintapp.apps.admin import admin
from blueprintapp.apps.frontend import frontend
app.register_blueprint(admin)
app.register_blueprint(frontend)

@app.route('/app_level')
def app_level_view():
    return render_template('index.html')
