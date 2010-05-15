# -*- coding: utf-8 -*-
from urlparse import urljoin
from flask import Module, render_template, request, flash, abort, redirect, \
     g, url_for
from werkzeug.contrib.atom import AtomFeed
from flask_website.utils import requires_login, requires_admin, format_creole
from flask_website.database import Category, Snippet, Comment, db_session

snippets = Module(__name__, url_prefix='/snippets')


@snippets.route('/')
def index():
    return render_template('snippets/index.html',
        categories=Category.query.order_by(Category.name).all(),
        recent=Snippet.query.order_by(Snippet.pub_date.desc()).limit(5).all())


@snippets.route('/new/', methods=['GET', 'POST'])
@requires_login
def new():
    category_id = None
    preview = None
    if 'category' in request.args:
        rv = Category.query.filter_by(slug=request.args['category']).first()
        if rv is not None:
            category_id = rv.id
    if request.method == 'POST':
        category_id = request.form.get('category', type=int)
        if 'preview' in request.form:
            preview = format_creole(request.form['body'])
        else:
            title = request.form['title']
            body = request.form['body']
            if not body:
                flash(u'Error: you have to enter a snippet')
            else:
                category = Category.query.get(category_id)
                if category is not None:
                    snippet = Snippet(g.user, title, body, category)
                    db_session.add(snippet)
                    db_session.commit()
                    flash(u'Your snippet was added')
                    return redirect(snippet.url)
    return render_template('snippets/new.html',
        categories=Category.query.order_by(Category.name).all(),
        active_category=category_id, preview=preview)


@snippets.route('/<int:id>/', methods=['GET', 'POST'])
def show(id):
    snippet = Snippet.query.get(id)
    if snippet is None:
        abort(404)
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']
        if not text:
            flash(u'Error: the text is required')
        else:
            db_session.add(Comment(snippet, g.user, title, text))
            db_session.commit()
            flash(u'Your comment was added')
            return redirect(snippet.url)
    return render_template('snippets/show.html', snippet=snippet)


@snippets.route('/edit/<int:id>/', methods=['GET', 'POST'])
@requires_login
def edit(id):
    snippet = Snippet.query.get(id)
    if snippet is None:
        abort(404)
    if g.user is None or (not g.user.is_admin and snippet.author != g.user):
        abort(401)
    preview = None
    form = dict(title=snippet.title, body=snippet.body,
                category=snippet.category.id)
    if request.method == 'POST':
        form['title'] = request.form['title']
        form['body'] = request.form['body']
        form['category'] = request.form.get('category', type=int)
        if 'preview' in request.form:
            preview = format_creole(request.form['body'])
        elif 'delete' in request.form:
            for comment in snippet.comments:
                db_session.delete(comment)
            db_session.delete(snippet)
            db_session.commit()
            flash(u'Your snippet was deleted')
            return redirect(url_for('snippets.index'))
        else:
            category_id = request.form.get('category', type=int)
            if not form['body']:
                flash(u'Error: you have to enter a snippet')
            else:
                category = Category.query.get(category_id)
                if category is not None:
                    snippet.title = form['title']
                    snippet.body = form['body']
                    snippet.category = category
                    db_session.commit()
                    flash(u'Your snippet was modified')
                    return redirect(snippet.url)
    return render_template('snippets/edit.html',
        snippet=snippet, preview=preview, form=form,
        categories=Category.query.order_by(Category.name).all())


@snippets.route('/category/<slug>/')
def category(slug):
    category = Category.query.filter_by(slug=slug).first()
    if category is None:
        abort(404)
    snippets = category.snippets.order_by(Snippet.title).all()
    return render_template('snippets/category.html', category=category,
                           snippets=snippets)


@snippets.route('/manage-categories/', methods=['GET', 'POST'])
@requires_admin
def manage_categories():
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        for category in categories:
            category.name = request.form['name.%d' % category.id]
            category.slug = request.form['slug.%d' % category.id]
        db_session.commit()
        flash(u'Categories updated')
        return redirect(url_for('manage_categories'))
    return render_template('snippets/manage_categories.html',
                           categories=categories)


@snippets.route('/new-category/', methods=['POST'])
@requires_admin
def new_category():
    category = Category(name=request.form['name'])
    db_session.add(category)
    db_session.commit()
    flash(u'Category %s created.' % category.name)
    return redirect(url_for('manage_categories'))


@snippets.route('/delete-category/<int:id>/', methods=['GET', 'POST'])
@requires_admin
def delete_category(id):
    category = Category.query.get(id)
    if category is None:
        abort(404)
    if request.method == 'POST':
        if 'cancel' in request.form:
            flash(u'Deletion was aborted')
            return redirect(url_for('manage_categories'))
        move_to_id = request.form.get('move_to', type=int)
        if move_to_id:
            move_to = Category.query.get(move_to_id)
            if move_to is None:
                flash(u'Category was removed in the meantime')
            else:
                for snippet in category.snippets.all():
                    snippet.category = move_to
                db_session.delete(category)
                flash(u'Category %s deleted and entries moved to %s.' %
                      (category.name, move_to.name))
        else:
            category.snippets.delete()
            db_session.delete(category)
            flash(u'Category %s deleted' % category.name)
        db_session.commit()
        return redirect(url_for('manage_categories'))
    return render_template('snippets/delete_category.html',
                           category=category,
                           other_categories=Category.query
                              .filter(Category.id != category.id).all())


@snippets.route('/recent.atom')
def recent_feed():
    feed = AtomFeed(u'Recent Flask Snippets',
                    subtitle=u'Recent additions to the Flask snippet archive',
                    feed_url=request.url, url=request.url_root)
    snippets = Snippet.query.order_by(Snippet.pub_date.desc()).limit(15)
    for snippet in snippets:
        feed.add(snippet.title, unicode(snippet.rendered_body),
                 content_type='html', author=snippet.author.name,
                 url=urljoin(request.url_root, snippet.url),
                 updated=snippet.pub_date)
    return feed.get_response()


@snippets.route('/snippets/<int:id>/comments.atom')
def comments_feed(id):
    snippet = Snippet.query.get(id)
    if snippet is None:
        abort(404)
    feed = AtomFeed(u'Comments for Snippet “%s”' % snippet.title,
                    feed_url=request.url, url=request.url_root)
    for comment in snippet.comments:
        feed.add(comment.title or u'Untitled Comment',
                 unicode(snippet.rendered_text),
                 content_type='html', author=comment.author.name,
                 url=request.url, updated=comment.pub_date)
    return feed.get_response()
