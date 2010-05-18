from flask import Module, render_template
from flask_website.twitter import flask_tweets

community = Module(__name__, url_prefix='/community')

@community.route('/')
def index():
    return render_template('community/index.html')


@community.route('/irc/')
def irc():
    return render_template('community/irc.html')


@community.route('/twitter/')
def twitter():
    return render_template('community/twitter.html', tweets=flask_tweets)


@community.route('/badges/')
def badges():
    return render_template('community/badges.html')


@community.route('/logos/')
def logos():
    return render_template('community/logos.html')
