# -*- coding: utf-8 -*-
import os
from whoosh import highlight, analysis, qparser
from whoosh.support.charset import accent_map
from flask import Markup
from flask_website import app
from werkzeug import import_string


def open_index():
    from whoosh import index, fields as f
    if os.path.isdir(app.config['WHOOSH_INDEX']):
        return index.open_dir(app.config['WHOOSH_INDEX'])
    os.mkdir(app.config['WHOOSH_INDEX'])
    analyzer = analysis.StemmingAnalyzer() | analysis.CharsetFilter(accent_map)
    schema = f.Schema(
        url=f.ID(stored=True, unique=True),
        id=f.ID(stored=True),
        title=f.TEXT(stored=True, field_boost=2.0, analyzer=analyzer),
        type=f.ID(stored=True),
        keywords=f.KEYWORD(commas=True),
        content=f.TEXT(analyzer=analyzer)
    )
    return index.create_in(app.config['WHOOSH_INDEX'], schema)


index = open_index()


class Indexable(object):
    search_document_kind = None

    def add_to_search_index(self, writer):
        writer.add_document(url=unicode(self.url),
                            type=self.search_document_type,
                            **self.get_search_document())

    @classmethod
    def describe_search_result(cls, result):
        return None

    @property
    def search_document_type(self):
        cls = type(self)
        return cls.__module__ + u'.' + cls.__name__

    def get_search_document(self):
        raise NotImplementedError()

    def remove_from_search_index(self, writer):
        writer.delete_by_term('url', unicode(self.url))


def highlight_all(result, field):
    text = result[field]
    return Markup(highlight.Highlighter(
        fragmenter=highlight.WholeFragmenter(),
        formatter=result.results.highlighter.formatter)
            .highlight_hit(result, field, text=text)) or text


class SearchResult(object):

    def __init__(self, result):
        self.url = result['url']
        self.title_text = result['title']
        self.title = highlight_all(result, 'title')
        cls = import_string(result['type'])
        self.kind = cls.search_document_kind
        self.description = cls.describe_search_result(result)


class SearchResultPage(object):

    def __init__(self, results, page):
        self.page = page
        if results is None:
            self.results = []
            self.pages = 1
            self.total = 0
        else:
            self.results = [SearchResult(r) for r in results]
            self.pages = results.pagecount
            self.total = results.total

    def __iter__(self):
        return iter(self.results)


def search(query, page=1, per_page=20):
    with index.searcher() as s:
        qp = qparser.MultifieldParser(['title', 'content'], index.schema)
        q = qp.parse(unicode(query))
        try:
            result_page = s.search_page(q, page, pagelen=per_page)
        except ValueError:
            if page == 1:
                return SearchResultPage(None, page)
            return None
        results = result_page.results
        results.highlighter.fragmenter.maxchars = 512
        results.highlighter.fragmenter.surround = 40
        results.highlighter.formatter = highlight.HtmlFormatter('em',
            classname='search-match', termclass='search-term',
            between=u'<span class=ellipsis> … </span>')
        return SearchResultPage(result_page, page)


def update_model_based_indexes(session, flush_context):
    """Called by a session event, updates the model based documents."""
    to_delete = []
    to_add = []
    for model in session.new:
        if isinstance(model, Indexable):
            to_add.append(model)

    for model in session.dirty:
        if isinstance(model, Indexable):
            to_delete.append(model)
            to_add.append(model)

    for model in session.dirty:
        if isinstance(model, Indexable):
            to_delete.append(model)

    if not (to_delete or to_add):
        return

    writer = index.writer()
    for model in to_delete:
        model.remove_from_search_index(writer)
    for model in to_add:
        model.add_to_search_index(writer)
    writer.commit()


def update_documentation_index():
    from flask_website.docs import DocumentationPage
    writer = index.writer()
    for page in DocumentationPage.iter_pages():
        page.remove_from_search_index(writer)
        page.add_to_search_index(writer)
    writer.commit()


def reindex_snippets():
    from flask_website.database import Snippet
    writer = index.writer()
    for snippet in Snippet.query.all():
        snippet.remove_from_search_index(writer)
        snippet.add_to_search_index(writer)
    writer.commit()
