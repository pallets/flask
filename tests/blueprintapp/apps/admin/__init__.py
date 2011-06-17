from flask import Blueprint, render_template

admin = Blueprint(__name__, url_prefix='/admin')


@admin.route('/')
def index():
    return render_template('admin/index.html')


@admin.route('/index2')
def index2():
    return render_template('./admin/index.html')
