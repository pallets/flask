# -*- coding: utf-8 -*-
import os
import re
from flask import url_for, Markup
from flask_website import app
from flask_website.search import Indexable


_doc_body_re = re.compile(r'''(?smx)
    <title>(.*?)</title>.*?
    <div\s+class="body">(.*?)<div\s+class="sphinxsidebar">
''')


class DocumentationPage(Indexable):
    search_document_kind = 'documentation'

    def __init__(self, slug):
        self.slug = slug
        fn = os.path.join(app.config['DOCUMENTATION_PATH'],
                          slug, 'index.html')
        with open(fn) as f:
            contents = f.read().decode('utf-8')
            title, text = _doc_body_re.search(contents).groups()
        self.title = Markup(title).striptags().split(u'—')[0].strip()
        self.text = Markup(text).striptags().strip().replace(u'¶', u'')

    def get_search_document(self):
        return dict(
            id=unicode(self.slug),
            title=self.title,
            keywords=[],
            content=self.text
        )

    @property
    def url(self):
        return url_for('docs.show', page=self.slug)

    @classmethod
    def describe_search_result(cls, result):
        rv = cls(result['id'])
        return Markup(result.highlights('content', text=rv.text)) or None

    @classmethod
    def iter_pages(cls):
        base_folder = os.path.abspath(app.config['DOCUMENTATION_PATH'])
        for dirpath, dirnames, filenames in os.walk(base_folder):
            if 'index.html' in filenames:
                slug = dirpath[len(base_folder) + 1:]
                # skip the index page.  useless
                if slug:
                    yield DocumentationPage(slug)
