from flask import Module, render_template

snippets = Module(__name__, url_prefix='/snippets')


@snippets.route('/')
def index():
    return render_template('snippets/index.html')
