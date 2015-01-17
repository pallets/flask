# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.sessions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Added tests for the sessions.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import unittest
import shutil
from tempfile import mkdtemp, gettempdir

from werkzeug.testsuite import WerkzeugTestCase
from werkzeug.contrib.sessions import FilesystemSessionStore



class SessionTestCase(WerkzeugTestCase):

    def setup(self):
        self.session_folder = mkdtemp()

    def teardown(self):
        shutil.rmtree(self.session_folder)

    def test_default_tempdir(self):
        store = FilesystemSessionStore()
        assert store.path == gettempdir()

    def test_basic_fs_sessions(self):
        store = FilesystemSessionStore(self.session_folder)
        x = store.new()
        assert x.new
        assert not x.modified
        x['foo'] = [1, 2, 3]
        assert x.modified
        store.save(x)

        x2 = store.get(x.sid)
        assert not x2.new
        assert not x2.modified
        assert x2 is not x
        assert x2 == x
        x2['test'] = 3
        assert x2.modified
        assert not x2.new
        store.save(x2)

        x = store.get(x.sid)
        store.delete(x)
        x2 = store.get(x.sid)
        # the session is not new when it was used previously.
        assert not x2.new

    def test_non_urandom(self):
        urandom = os.urandom
        del os.urandom
        try:
            store = FilesystemSessionStore(self.session_folder)
            store.new()
        finally:
            os.urandom = urandom


    def test_renewing_fs_session(self):
        store = FilesystemSessionStore(self.session_folder, renew_missing=True)
        x = store.new()
        store.save(x)
        store.delete(x)
        x2 = store.get(x.sid)
        assert x2.new

    def test_fs_session_lising(self):
        store = FilesystemSessionStore(self.session_folder, renew_missing=True)
        sessions = set()
        for x in range(10):
            sess = store.new()
            store.save(sess)
            sessions.add(sess.sid)

        listed_sessions = set(store.list())
        assert sessions == listed_sessions


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SessionTestCase))
    return suite
