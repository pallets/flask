from flask import Module, render_template


admin = Module(__name__, url_prefix='/admin')


@admin.route('/')
def index():
    return render_template('admin/index.html')


@admin.route('/index2')
def index2():
    return render_template('./admin/index.html')
