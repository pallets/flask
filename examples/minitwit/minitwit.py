# -*- coding: utf-8 -*-
from __future__ import with_statement
import re
import time
import sqlite3
from hashlib import md5
from datetime import datetime
from contextlib import closing
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, generate_password_hash, \
     check_password_hash


# configuration
DATABASE = '/tmp/minitwit.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

# create our little application :)
app = Flask(__name__)


def connect_db():
    """Returns a new database connection to the database."""
    return sqlite3.connect(DATABASE)


def init_db():
    """Creates the database tables."""
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


def get_user_id(username):
    """Convenience method to look up the id for a username"""
    rv = g.db.execute('select user_id from user where username = ?',
                       [username]).fetchone()
    return rv[0] if rv else None


def format_datetime(timestamp):
    """Format a timestamp for display"""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


def gravatar_url(email, size=80):
    """Return the gravatar image for the given email address"""
    return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
        (md5(email.lower().encode('utf-8')).hexdigest(), size)


@app.request_init
def before_request():
    """Make sure we are connected to the database each request and look
    up the current user so that we know he's there.
    """
    g.db = sqlite3.connect(DATABASE)
    if 'user_id' in session:
        g.user = query_db('select * from user where user_id = ?',
                          [session['user_id']], one=True)


@app.request_shutdown
def after_request(request):
    """Closes the database again at the end of the request."""
    g.db.close()
    return request


@app.route('/')
def timeline():
    if not 'user_id' in session:
        return redirect(url_for('public_timeline'))
    offset = request.args.get('offset', type=int)
    return render_template('timeline.html', messages=query_db('''
        select message.*, user.* from message, user
        where message.author_id = user.user_id and (
            user.user_id = ? or
            user.user_id in (select whom_id from follower
                                    where who_id = ?))
        order by message.pub_date desc limit ?''',
        [session['user_id'], session['user_id'], PER_PAGE]))


@app.route('/public')
def public_timeline():
    return render_template('timeline.html', messages=query_db('''
        select message.*, user.* from message, user
        where message.author_id = user.user_id
        order by message.pub_date desc limit ?''', [PER_PAGE]))


@app.route('/<username>')
def user_timeline(username):
    profile_user = query_db('select * from user where username = ?',
                            [username], one=True)
    if profile_user is None:
        abort(404)
    followd = False
    if 'user_id' in session:
        followed = query_db('''select 1 from follower where
            follower.who_id = ? and follower.whom_id = ?''',
            [session['user_id'], profile_user['user_id']], one=True) is not None
    return render_template('timeline.html', messages=query_db('''
            select message.*, user.* from message, user where
            user.user_id = message.author_id and user.user_id = ?
            order by message.pub_date desc limit ?''',
            [profile_user['user_id'], PER_PAGE]), followed=followed,
            profile_user=profile_user)


@app.route('/<username>/follow')
def follow_user(username):
    if not 'user_id' in session:
        abort(401)
    whom_id = get_user_id(username)
    if whom_id is None:
        abort(404)
    g.db.execute('insert into follower (who_id, whom_id) values (?, ?)',
                [session['user_id'], whom_id])
    g.db.commit()
    flash('You are now following "%s"' % username)
    return redirect(url_for('user_timeline', username=username))


@app.route('/<username>/unfollow')
def unfollow_user(username):
    if not 'user_id' in session:
        abort(401)
    whom_id = get_user_id(username)
    if whom_id is None:
        abort(404)
    g.db.execute('delete from follower where who_id=? and whom_id=?',
                [session['user_id'], whom_id])
    g.db.commit()
    flash('You are no longer following "%s"' % username)
    return redirect(url_for('user_timeline', username=username))


@app.route('/add_message')
def add_message():
    if 'user_id' not in session:
        abort(401)
    if request.form['text']:
        g.db.execute('''insert into message (author_id, text, pub_date)
            values (?, ?, ?)''', (session['user_id'], request.form['text'],
                                  int(time.time())))
        g.db.commit()
        flash('Your message was recorded')
    return redirect(url_for('timeline'))


@app.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        user = query_db('''select * from user where
            username = ?''', [request.form['username']], one=True)
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['pw_hash'],
                                     request.form['password']):
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['user_id'] = user['user_id']
            return redirect(url_for('timeline'))
    return render_template('login.html', error=error)


@app.route('/register')
def register():
    if 'user_id' in session:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or \
                 '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords to not match'
        elif get_user_id(request.form['username']) is not None:
            error = 'The username is already taken'
        else:
            g.db.execute('''insert into user (
                username, email, pw_hash) values (?, ?, ?)''',
                [request.form['username'], request.form['email'],
                 generate_password_hash(request.form['password'])])
            g.db.commit()
            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('public_timeline'))


# add some filters to jinja and set the secret key and debug mode
# from the configuration.
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['gravatar'] = gravatar_url
app.secret_key = SECRET_KEY
app.debug = DEBUG


if __name__ == '__main__':
    app.run()
