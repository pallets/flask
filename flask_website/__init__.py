from flask import Flask, session, g, render_template
from flaskext.openid import OpenID

app = Flask(__name__)
app.config.from_object('websiteconfig')

from flask_website.openid_auth import DatabaseOpenIDStore
oid = OpenID(app, store_factory=DatabaseOpenIDStore)


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.before_request
def load_current_user():
    g.user = User.query.filter_by(openid=session['openid']).first() \
        if 'openid' in session else None


@app.teardown_request
def remove_db_session(exception):
    db_session.remove()


app.add_url_rule('/docs/', endpoint='docs.index', build_only=True)
app.add_url_rule('/docs/<path:page>/', endpoint='docs.show',
                 build_only=True)
app.add_url_rule('/docs/flask-docs.pdf', endpoint='docs.pdf',
                 build_only=True)
app.add_url_rule('/docs/flask-docs.zip', endpoint='docs.zip',
                 build_only=True)

from flask_website.views import general
from flask_website.views import community
from flask_website.views import mailinglist
from flask_website.views import snippets
from flask_website.views import extensions
app.register_blueprint(general.mod)
app.register_blueprint(community.mod)
app.register_blueprint(mailinglist.mod)
app.register_blueprint(snippets.mod)
app.register_blueprint(extensions.mod)

from flask_website.database import User, db_session
from flask_website import utils

app.jinja_env.filters['datetimeformat'] = utils.format_datetime
app.jinja_env.filters['timedeltaformat'] = utils.format_timedelta
app.jinja_env.filters['displayopenid'] = utils.display_openid
