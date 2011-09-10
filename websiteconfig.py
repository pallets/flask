import os

_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = False

SECRET_KEY = 'testkey'
DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'flask-website.db')
DATABASE_CONNECT_OPTIONS = {}
ADMINS = frozenset(['http://lucumr.pocoo.org/'])

THREADS_PER_PAGE = 15
MAILINGLIST_PATH = os.path.join(_basedir, '_mailinglist')
INCOMING_MAIL_FOLDER = '_mailinglist/incoming'
THREAD_FOLDER = '_mailinglist/threads'
LIST_NAME = 'flask'
RSYNC_PATH = 'librelist.com::json/%s'
SUBJECT_PREFIX = '[flask]'
WHOOSH_INDEX = os.path.join(_basedir, 'flask-website.whoosh')
DOCUMENTATION_PATH = os.path.join(_basedir, '../flask/docs/_build/dirhtml')

del os
