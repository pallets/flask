from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, \
     String, DateTime, ForeignKey
from sqlalchemy.orm import scoped_session, sessionmaker, backref
from sqlalchemy.ext.declarative import declarative_base

from flask_website import config

engine = create_engine(config.DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

def init_db():
    Model.metadata.create_all(bind=engine)


class Model(declarative_base()):
    query = db_session.query_property()


class User(Model):
    __tablename__ = 'users'
    id = Column('user_id', Integer, primary_key=True)
    openid = Column('openid', String(200))
    username = Column(String(40), unique=True)
    password = Column(String(80))

    def __init__(self, username, password):
        self.username = username
        self.password = password


class Category(Model):
    __tablename__ = 'categories'
    id = Column('category_id', Integer, primary_key=True)
    name = Column(String(50))
    slug = Column(String(50))


class Snippet(Model):
    __tablename__ = 'snippets'
    id = Column('snippet_id', Integer, primary_key=True)
    author = ForeignKey(User, backref=backref('snippets', lazy='dynamic'))
    category = ForeignKey(Category, backref=backref('snippets', lazy='dynamic'))
    title = Column(String(200))
    body = Column(String)
    pub_date = DateTime()

    def __init__(self, author, title, body):
        self.author = author
        self.title = title
        self.body = body
        self.pub_date = datetime.utcnow()


class Comment(Model):
    __tablename__ = 'comments'
    id = Column('comment_id', Integer, primary_key=True)
    snippet = ForeignKey(Snippet, backref='lazy')
    author = ForeignKey(User, backref=backref('comments', lazy='dynamic'))
    title = Column(String(200))
    text = Column(String)
    pub_date = DateTime()

    def __init__(self, author, title, text):
        self.author = author
        self.title = title
        self.text = text
        self.pub_date = datetime.utcnow()


class OpenIDAssociation(Model):
    id = Column('association_id', Integer, primary_key=True)
    server_url = Column(String(1024))
    handle = Column(String(255))
    secret = Column(String(255))
    issued = Column(Integer)
    lifetime = Column(Integer)
    assoc_type = Column(String(64))


class OpenIDUserNonces(Model):
    id = Column('user_nonce_id', Integer, primary_key=True)
    server_url = Column(String(1024))
    timestamp = Column(Integer)
    salt = Column(String(40))
