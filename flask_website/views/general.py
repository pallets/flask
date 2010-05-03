from flask import Module, render_template, session, redirect, url_for, \
     request, flash, g, Response
from flask_website import openid_auth
from flask_website.database import db_session, User

general = Module(__name__)


@general.route('/')
def index():
    return render_template('general/index.html')


@general.route('/logout/')
def logout():
    if 'openid' in session:
        flash(u'Logged out')
        del session['openid']
    return redirect(request.referrer or url_for('general.index'))


@general.route('/login/', methods=['GET', 'POST'])
def login():
    if g.user is not None:
        return redirect(url_for('general.index'))
    rv = openid_auth.check_return_from_provider()
    if rv is not None:
        return rv
    if request.method == 'POST':
        openid = request.values.get('openid')
        if openid:
            return openid_auth.login(openid)
    return render_template('general/login.html')


@general.route('/first-login/', methods=['GET', 'POST'])
def first_login():
    if g.user is not None or 'openid' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'cancel' in request.form:
            del session['openid']
            flash(u'Login was aborted')
            return redirect(url_for('general.login'))
        db_session.add(User(request.form['name'], session['openid']))
        db_session.commit()
        flash(u'Successfully created profile and logged in')
        return openid_auth.redirect_back()
    return render_template('general/first_login.html',
                           openid=session['openid'])
