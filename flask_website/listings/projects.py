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

    def to_json(self):
        rv = vars(self).copy()
        rv['description'] = unicode(rv['description'])
        return rv


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
        '''),
        Project('Meetup Meeter', 'http://meetupmeeter.com/', u'''
            <p>
              Meetup Meeter is a tool for you to know who you have and have not
              met at a particular meetup event.
        '''),
        Project('newsmeme', 'http://thenewsmeme.com/', u'''
            <p>
              A hackernews/reddit clone written with Flask and
              various Flask extensions.
        ''', source='http://bitbucket.org/danjac/newsmeme'),
        Project('ymasuda.jp', 'http://ymasuda.jp/', u'''
            <p>
              Personal website of Yasushi Masuda.
        '''),
        Project('Python DoJoe', 'http://pythondojoe.appspot.com/', u'''
            <p>
              Website of Python DoJoe - a gathering of Python hackers
        '''),
        Project('Steven Harms\' Website', 'http://www.sharms.org/', u'''
            <p>
              Personal website of Steven Harms.
        ''', source='http://github.com/sharms/HomePage'),
        Project('einfachJabber.de', 'http://einfachjabber.de', u'''
            <p>
              Website of a German jabber community.
        '''),
        Project('ThadeusB\'s Website', 'http://thadeusb.com/', u'''
            <p>
              Personal website of ThadeusB.
        '''),
        Project('learnbuffet.com', 'http://www.learnbuffett.com/', u'''
            <p>
              Learn trading and make significant profits statistically.
        '''),
        Project('was it up?', 'http://wasitup.com/', u'''
            <p>
              A website monitoring service.
        '''),
        Project('Eugen\'s Blog', 'http://blog.eugenkiss.com/', u'''
            <p>
              Personal Website of Eugen Kiss.
        ''', source='http://github.com/eugenkiss/Simblin'),
        Project('Blueslug', 'http://blueslug.com/', u'''
            <p>
              A flask-powered anti-social delicious clone
        '''),
        Project('Comiker', 'http://www.comiker.com/', u'''
            <p>
              A website where you can create webcomics and vote for the
              best ones.
        '''),
        Project('weluse GmbH', 'http://weluse.de/', u'''
            <p>
              A German corporate website.
        '''),
        Project('Papyrus Research', 'http://www.papyrusresearch.com/', u'''
            <p>
              The website of Papyrus Research, a market research company.
        '''),
        Project('Viewfinder', 'http://viewfinder.io/', u'''
            <p>
              A website that helps you find photos you'll like on Flickr.
        '''),
        Project('Daily Lyric', 'http://dailylyric.appspot.com/', u'''
            <p>
              Gives a random song lyric every day
        '''),
        Project('Nexuo Community', 'http://community.nuxeo.com/', u'''
            <p>
              Activity stream aggregator and umbrella home page for the Nuxeo
              Open Source ECM project sites.
        ''', source='https://github.com/sfermigier/nuxeo.org'),
        Project('Planete GT LL', 'http://www.gt-logiciel-libre.org/', u'''
            <p>
              News aggregator for the open source workgroup of the Paris Region
              innovation cluster, Systematic.
        ''', source='https://github.com/sfermigier/Planet-GTLL'),
        Project('Battlefield3 Development News Aggregator',
                'http://bf3.immersedcode.org/', u'''
            <p>
              Development news aggregator for Battlefield3.  Tracks twitter
              accounts and forum posts by DICE developers.
        ''', source='https://github.com/mitsuhiko/bf3-aggregator'),
        Project('Media Queries', 'http://mediaqueri.es/', u'''
            <p>
              A collection of responsive web designs.
        '''),
        Project('Life Short, Coding More', 'http://www.liul.net/', u'''
            <p>
              Personal blog.
        '''),
        Project('Flask Feedback', 'http://feedback.flask.pocoo.org/', u'''
            <p>
              Website by the Flask project that collects feedback from
              users.
        ''', source='https://github.com/mitsuhiko/flask-feedback')
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
        ''', source='http://bitbucket.org/esaurito/ubersuggest'),
        Project(u'@font-face { … }', 'http://fontface.kr/', u'''
            <p>
              @font-face is a web font hosting service for Hangul
              fonts.
        '''),
        Project('Have they emailed me?', 'http://emailed-me.appspot.com/', '''
            <p>
              A mini-site for checking Google's GMail feed with Oauth.
        ''', source='http://github.com/lincolnloop/emailed-me'),
        Project('Remar.kZ', 'http://remar.kz/', '''
            <p>
               Sometimes you use someone else's computer and find something
               neat and interesting.  Store it on Remar.kZ without having
               to enter your credentials.
        ''', source='http://bitbucket.org/little_arhat/remarkz'),
        Project('Dominion', 'http://alexanderweb.de:8080/', u'''
            <p>
              Domination is a clone of a well-known card game.
        ''', source='https://bitbucket.org/xoraxax/domination/'),
        Project('jitviewer', 'https://bitbucket.org/pypy/jitviewer', '''
            <p>
              web-based tool to inspect the output of PyPy JIT log
        ''')
    ]
}


# order projects by name
for _category in projects.itervalues():
    _category.sort(key=lambda x: x.name.lower())
del _category
