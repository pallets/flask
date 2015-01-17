#!/usr/bin/env python

from os import environ
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class Heroku(object):
    """Heroku configurations for flask."""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        # SQL-Alchemy
        app.config.setdefault('SQLALCHEMY_DATABASE_URI', environ.get('DATABASE_URL'))

        # Sentry
        app.config.setdefault('SENTRY_DSN', environ.get('SENTRY_DSN'))

        # Exceptional
        app.config.setdefault('EXCEPTIONAL_API_KEY', environ.get('EXCEPTIONAL_API_KEY'))

        # Flask-GoogleFed
        app.config.setdefault('GOOGLE_DOMAIN', environ.get('GOOGLE_DOMAIN'))

        # Celery w/ RabbitMQ
        if 'RABBITMQ_URL' in environ:
            app.config.setdefault('BROKER_URL', environ.get('RABBITMQ_URL'))
        # Celery w/ RedisCloud
        elif 'REDISCLOUD_URL' in environ:
            app.config.setdefault('BROKER_URL', environ.get('REDISCLOUD_URL'))
            app.config.setdefault('BROKER_TRANSPORT', environ.get('REDISCLOUD_URL'))

        # Mailgun
        if 'MAILGUN_SMTP_SERVER' in environ:
            app.config.setdefault('SMTP_SERVER', environ.get('MAILGUN_SMTP_SERVER'))
            app.config.setdefault('SMTP_LOGIN', environ.get('MAILGUN_SMTP_LOGIN'))
            app.config.setdefault('SMTP_PASSWORD', environ.get('MAILGUN_SMTP_PASSWORD'))
            app.config.setdefault('MAIL_SERVER', environ.get('MAILGUN_SMTP_SERVER'))
            app.config.setdefault('MAIL_USERNAME', environ.get('MAILGUN_SMTP_LOGIN'))
            app.config.setdefault('MAIL_PASSWORD', environ.get('MAILGUN_SMTP_PASSWORD'))
            app.config.setdefault('MAIL_USE_TLS', True)
        # SendGrid
        elif 'SENDGRID_USERNAME' in environ:
            app.config.setdefault('SMTP_SERVER', 'smtp.sendgrid.net')
            app.config.setdefault('SMTP_LOGIN', environ.get('SENDGRID_USERNAME'))
            app.config.setdefault('SMTP_PASSWORD', environ.get('SENDGRID_PASSWORD'))
            app.config.setdefault('MAIL_SERVER', 'smtp.sendgrid.net')
            app.config.setdefault('MAIL_USERNAME', environ.get('SENDGRID_USERNAME'))
            app.config.setdefault('MAIL_PASSWORD', environ.get('SENDGRID_PASSWORD'))
            app.config.setdefault('MAIL_USE_TLS', True)
        # Postmark
        elif 'POSTMARK_SMTP_SERVER' in environ:
            app.config.setdefault('SMTP_SERVER', 'POSTMARK_SMTP_SERVER')
            app.config.setdefault('SMTP_LOGIN', environ.get('POSTMARK_API_KEY'))
            app.config.setdefault('SMTP_PASSWORD', environ.get('POSTMARK_API_KEY'))
            app.config.setdefault('MAIL_SERVER', 'POSTMARK_SMTP_SERVER')
            app.config.setdefault('MAIL_USERNAME', environ.get('POSTMARK_API_KEY'))
            app.config.setdefault('MAIL_PASSWORD', environ.get('POSTMARK_API_KEY'))
            app.config.setdefault('MAIL_USE_TLS', True)

        # Redis To Go
        redis_url = environ.get('REDISTOGO_URL')
        if redis_url:
            url = urlparse(redis_url)
            app.config.setdefault('REDIS_HOST', url.hostname)
            app.config.setdefault('REDIS_PORT', url.port)
            app.config.setdefault('REDIS_PASSWORD', url.password)

        # Mongolab
        mongolab_uri = environ.get('MONGOLAB_URI')
        if mongolab_uri:
            url = urlparse(mongolab_uri)
            app.config.setdefault('MONGO_URI', mongolab_uri)
            app.config.setdefault('MONGODB_USER', url.username)
            app.config.setdefault('MONGODB_PASSWORD', url.password)
            app.config.setdefault('MONGODB_HOST', url.hostname)
            app.config.setdefault('MONGODB_PORT', url.port)
            app.config.setdefault('MONGODB_DB', url.path[1:])

        # MongoHQ
        mongohq_uri = environ.get('MONGOHQ_URL')
        if mongohq_uri:
            url = urlparse(mongohq_uri)
            app.config.setdefault('MONGO_URI', mongohq_uri)
            app.config.setdefault('MONGODB_USER', url.username)
            app.config.setdefault('MONGODB_PASSWORD', url.password)
            app.config.setdefault('MONGODB_HOST', url.hostname)
            app.config.setdefault('MONGODB_PORT', url.port)
            app.config.setdefault('MONGODB_DB', url.path[1:])

        # Cloudant
        cloudant_uri = environ.get('CLOUDANT_URL')
        if cloudant_uri:
            app.config.setdefault('COUCHDB_SERVER', cloudant_uri)

        # Memcachier
        app.config.setdefault('CACHE_MEMCACHED_SERVERS', environ.get('MEMCACHIER_SERVERS'))
        app.config.setdefault('CACHE_MEMCACHED_USERNAME', environ.get('MEMCACHIER_USERNAME'))
        app.config.setdefault('CACHE_MEMCACHED_PASSWORD', environ.get('MEMCACHIER_PASSWORD'))
