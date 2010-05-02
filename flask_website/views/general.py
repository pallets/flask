from flask import Module, render_template

general = Module(__name__)


@general.route('/')
def index():
    return render_template('general/index.html')
