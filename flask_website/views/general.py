from flask import Module, render_template, session, redirect, url_for, \
     request, flash, g, Response
from flask_website import oid, twitter
from flask_website.database import db_session, User

general = Module(__name__)
tweets = twitter.SearchQuery(required=['flask'],
                             optional=['code', 'web', 'python', 'py',
                                       'pocoo', 'micro', 'mitsuhiko',
                                       'framework', 'django', 'jinja',
                                       'werkzeug', 'pylons'],
                             lang='en')


@general.route('/')
def index():
    return render_template('general/index.html', tweets=tweets)


@general.route('/logout/')
def logout():
    if 'openid' in session:
        flash(u'Logged out')
        del session['openid']
    return redirect(request.referrer or url_for('general.index'))


@general.route('/login/', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(url_for('general.index'))
    if request.method == 'POST':
        openid = request.values.get('openid')
        if openid:
            return oid.try_login(openid, ask_for=['fullname', 'nickname'])
    error = oid.fetch_error()
    if error:
        flash(u'Error: ' + error)
    return render_template('general/login.html', next=oid.get_next_url())


@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    user = User.query.filter_by(openid=resp.identity_url).first()
    if user is not None:
        flash(u'Successfully signed in')
        g.user = user
        return redirect(oid.get_next_url())
    return redirect(url_for('first_login', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname))


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
        return redirect(oid.get_next_url())
    return render_template('general/first_login.html',
                           next=oid.get_next_url(),
                           openid=session['openid'])
