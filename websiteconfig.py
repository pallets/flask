import os

_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = False
SECRET_KEY = 'testkey'
DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'flask-website.db')
MAILINGLIST_PATH = os.path.join(_basedir, '_mailinglist')
THREADS_PER_PAGE = 15

del os
