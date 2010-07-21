# -*- coding: utf-8 -*-
from urlparse import urlparse
from flask import Markup


class Project(object):

    def __init__(self, name, url, description, source=None):
        self.name = name
        self.url = url
        self.description = Markup(description)
        self.source = source

    @property
    def host(self):
        return urlparse(self.url)[1]

    @property
    def sourcehost(self):
        if self.source is not None:
            return urlparse(self.source)[1]


projects = {
    'websites': [
        Project('Flask Website', 'http://flask.pocoo.org/', '''
            <p>
              The website of the Flask microframework itself including the
              mailinglist interface, snippet archive and extension registry.
        '''),
        Project('Brightonpy', 'http://brightonpy.org/', '''
            <p>
              The website of the Brighton Python User Group
        ''', source='http://github.com/j4mie/brightonpy.org/'),
        Project('vlasiku.lojban.org', 'http://vlasisku.lojban.org/', '''
            <p>
              An intelligent search engine for the Lojban dictionary.
        '''),
        Project(u's h o r e … software development', 'http://shore.be/', '''
            <p>Corporate website of Shore Software Development.
        '''),
        # this one might change URL soon, check on each update
        Project('rdrei.net', 'http://new.rdrei.net/', '''
            <p>Personal website of Pascal Hartig.
        '''),
        Project(u'Ryde–Hunters HFFPS', 'http://rydehhffps.org.au/', u'''
            <p>The website of the Ryde–Hunters Hill Flora and Fauna Society.
        '''),
        Project('Red Bank Creative', 'http://www.redbankcreative.org/', '''
            <p>
              Local community meetup site for Red Bank, NJ powered
              by Flask and running on GAE.
        ''')
    ],
    'apps': [
        Project('960 Layout System', 'http://960ls.atomidata.com/', '''
            <p>
              The generator of the 960 Layout System is powered by Flask.  It
              generates downloadable 960 stylesheets.
        '''),
        Project('hg-review', 'http://review.stevelosh.com/', '''
            <p>
              hg-review is a code review system for Mercurial.  It is available
              GPL2 license.
        ''', source='http://bitbucket.org/sjl/hg-review/'),
        Project('geocron', 'http://geocron.us/', '''
            <p>
              By combining your present location with the time of day, geocron
              automates your life.
            <p>
              When you get to your Metro station during the commute home,
              geocron can send a text message reading "Pick me up dear" to your
              spouse.
        '''),
        Project('Cockerel', 'http://dcolish.github.com/Cockerel/', '''
            <p>An Online Logic Assistent Based on Coq.
        ''', source='http://github.com/dcolish/Cockerel'),
        Project('Ryshcate', 'http://ryshcate.leafstorm.us/', '''
            <p>
              Ryshcate is a Flask powered pastebin with sourcecode
              available.
        ''', source='http://bitbucket.org/leafstorm/ryshcate/'),
        Project(u'Übersuggest Keyword Suggestion Tool',
                'http://suggest.thinkpragmatic.net/', u'''
            <p>Übersuggest is a free tool that exploit the Google
            suggest JSON API to get keyword ideas for your search marketing
            campaign (PPC or SEO).
        ''', source='http://bitbucket.org/esaurito/ubersuggest')
    ]
}


# order projects by name
for _category in projects.itervalues():
    _category.sort(key=lambda x: x.name.lower())
del _category
