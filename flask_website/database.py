from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, \
     ForeignKey, event
from sqlalchemy.orm import scoped_session, sessionmaker, backref, relation
from sqlalchemy.ext.declarative import declarative_base

from werkzeug import cached_property, http_date

from flask import url_for, Markup
from flask_website import app, search

engine = create_engine(app.config['DATABASE_URI'],
                       convert_unicode=True,
                       **app.config['DATABASE_CONNECT_OPTIONS'])
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

def init_db():
    Model.metadata.create_all(bind=engine)


Model = declarative_base(name='Model')
Model.query = db_session.query_property()


class User(Model):
    __tablename__ = 'users'
    id = Column('user_id', Integer, primary_key=True)
    openid = Column('openid', String(200))
    name = Column(String(200))

    def __init__(self, name, openid):
        self.name = name
        self.openid = openid

    def to_json(self):
        return dict(name=self.name, is_admin=self.is_admin)

    @property
    def is_admin(self):
        return self.openid in app.config['ADMINS']

    def __eq__(self, other):
        return type(self) is type(other) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)


class Category(Model):
    __tablename__ = 'categories'
    id = Column('category_id', Integer, primary_key=True)
    name = Column(String(50))
    slug = Column(String(50))

    def __init__(self, name):
        self.name = name
        self.slug = '-'.join(name.split()).lower()

    def to_json(self):
        return dict(name=self.name, slug=self.slug, count=self.count)

    @cached_property
    def count(self):
        return self.snippets.count()

    @property
    def url(self):
        return url_for('snippets.category', slug=self.slug)


class Snippet(Model, search.Indexable):
    __tablename__ = 'snippets'
    id = Column('snippet_id', Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('users.user_id'))
    category_id = Column(Integer, ForeignKey('categories.category_id'))
    title = Column(String(200))
    body = Column(String)
    pub_date = Column(DateTime)

    author = relation(User, backref=backref('snippets', lazy='dynamic'))
    category = relation(Category, backref=backref('snippets', lazy='dynamic'))

    search_document_kind = 'snippet'

    def __init__(self, author, title, body, category):
        self.author = author
        self.title = title
        self.body = body
        self.category = category
        self.pub_date = datetime.utcnow()

    def to_json(self):
        return dict(id=self.id, title=self.title,
                    body=unicode(self.rendered_body),
                    pub_date=http_date(self.pub_date),
                    comments=[c.to_json() for c in self.comments],
                    author=self.author.to_json(),
                    category=self.category.slug)

    def get_search_document(self):
        return dict(
            id=unicode(self.id),
            title=self.title,
            keywords=[self.category.name],
            content=self.body
        )

    @classmethod
    def describe_search_result(cls, result):
        obj = cls.query.get(int(result['id']))
        if obj is not None:
            text = obj.rendered_body.striptags()
            return Markup(result.highlights('content', text=text)) or None

    @property
    def url(self):
        return url_for('snippets.show', id=self.id)

    @property
    def rendered_body(self):
        from flask_website.utils import format_creole
        return format_creole(self.body)


class Comment(Model):
    __tablename__ = 'comments'
    id = Column('comment_id', Integer, primary_key=True)
    snippet_id = Column(Integer, ForeignKey('snippets.snippet_id'))
    author_id = Column(Integer, ForeignKey('users.user_id'))
    title = Column(String(200))
    text = Column(String)
    pub_date = Column(DateTime)

    snippet = relation(Snippet, backref=backref('comments', lazy=True))
    author = relation(User, backref=backref('comments', lazy='dynamic'))

    def __init__(self, snippet, author, title, text):
        self.snippet = snippet
        self.author = author
        self.title = title
        self.text = text
        self.pub_date = datetime.utcnow()

    def to_json(self):
        return dict(author=self.author.to_json(),
                    title=self.title,
                    pub_date=http_date(self.pub_date),
                    text=unicode(self.rendered_text))

    @property
    def rendered_text(self):
        from flask_website.utils import format_creole
        return format_creole(self.text)


class OpenIDAssociation(Model):
    __tablename__ = 'openid_associations'
    id = Column('association_id', Integer, primary_key=True)
    server_url = Column(String(1024))
    handle = Column(String(255))
    secret = Column(String(255))
    issued = Column(Integer)
    lifetime = Column(Integer)
    assoc_type = Column(String(64))


class OpenIDUserNonce(Model):
    __tablename__ = 'openid_user_nonces'
    id = Column('user_nonce_id', Integer, primary_key=True)
    server_url = Column(String(1024))
    timestamp = Column(Integer)
    salt = Column(String(40))


event.listen(db_session, 'after_flush', search.update_model_based_indexes)
