from flask import Blueprint, render_template

frontend = Blueprint(__name__)


@frontend.route('/')
def index():
    return render_template('frontend/index.html')
