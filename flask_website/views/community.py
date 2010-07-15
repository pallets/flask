from flask import Module, render_template
from flask_website.twitter import flask_tweets
from flask_website.listings.projects import projects

mod = Module(__name__, url_prefix='/community')


@mod.route('/')
def index():
    return render_template('community/index.html')


@mod.route('/irc/')
def irc():
    return render_template('community/irc.html')


@mod.route('/twitter/')
def twitter():
    return render_template('community/twitter.html', tweets=flask_tweets)


@mod.route('/badges/')
def badges():
    return render_template('community/badges.html')


@mod.route('/poweredby/')
def poweredby():
    return render_template('community/poweredby.html', projects=projects)


@mod.route('/logos/')
def logos():
    return render_template('community/logos.html')
