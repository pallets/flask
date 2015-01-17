# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.security
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the security helpers.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import unittest

from werkzeug.testsuite import WerkzeugTestCase

from werkzeug.security import check_password_hash, generate_password_hash, \
     safe_join, pbkdf2_hex, safe_str_cmp


class SecurityTestCase(WerkzeugTestCase):

    def test_safe_str_cmp(self):
        assert safe_str_cmp('a', 'a') is True
        assert safe_str_cmp(b'a', u'a') is True
        assert safe_str_cmp('a', 'b') is False
        assert safe_str_cmp(b'aaa', 'aa') is False
        assert safe_str_cmp(b'aaa', 'bbb') is False
        assert safe_str_cmp(b'aaa', u'aaa') is True

    def test_password_hashing(self):
        hash0 = generate_password_hash('default')
        assert check_password_hash(hash0, 'default')
        assert hash0.startswith('pbkdf2:sha1:1000$')

        hash1 = generate_password_hash('default', 'sha1')
        hash2 = generate_password_hash(u'default', method='sha1')
        assert hash1 != hash2
        assert check_password_hash(hash1, 'default')
        assert check_password_hash(hash2, 'default')
        assert hash1.startswith('sha1$')
        assert hash2.startswith('sha1$')

        fakehash = generate_password_hash('default', method='plain')
        assert fakehash == 'plain$$default'
        assert check_password_hash(fakehash, 'default')

        mhash = generate_password_hash(u'default', method='md5')
        assert mhash.startswith('md5$')
        assert check_password_hash(mhash, 'default')

        legacy = 'md5$$c21f969b5f03d33d43e04f8f136e7682'
        assert check_password_hash(legacy, 'default')

        legacy = u'md5$$c21f969b5f03d33d43e04f8f136e7682'
        assert check_password_hash(legacy, 'default')

    def test_safe_join(self):
        assert safe_join('foo', 'bar/baz') == os.path.join('foo', 'bar/baz')
        assert safe_join('foo', '../bar/baz') is None
        if os.name == 'nt':
            assert safe_join('foo', 'foo\\bar') is None

    def test_pbkdf2(self):
        def check(data, salt, iterations, keylen, expected):
            rv = pbkdf2_hex(data, salt, iterations, keylen)
            self.assert_equal(rv, expected)

        # From RFC 6070
        check('password', 'salt', 1, None,
              '0c60c80f961f0e71f3a9b524af6012062fe037a6')
        check('password', 'salt', 1, 20,
              '0c60c80f961f0e71f3a9b524af6012062fe037a6')
        check('password', 'salt', 2, 20,
              'ea6c014dc72d6f8ccd1ed92ace1d41f0d8de8957')
        check('password', 'salt', 4096, 20,
              '4b007901b765489abead49d926f721d065a429c1')
        check('passwordPASSWORDpassword', 'saltSALTsaltSALTsaltSALTsaltSALTsalt',
              4096, 25, '3d2eec4fe41c849b80c8d83662c0e44a8b291a964cf2f07038')
        check('pass\x00word', 'sa\x00lt', 4096, 16,
              '56fa6aa75548099dcc37d7f03425e0c3')
        # This one is from the RFC but it just takes for ages
        ##check('password', 'salt', 16777216, 20,
        ## 'eefe3d61cd4da4e4e9945b3d6ba2158c2634e984')

        # From Crypt-PBKDF2
        check('password', 'ATHENA.MIT.EDUraeburn', 1, 16,
              'cdedb5281bb2f801565a1122b2563515')
        check('password', 'ATHENA.MIT.EDUraeburn', 1, 32,
              'cdedb5281bb2f801565a1122b25635150ad1f7a04bb9f3a333ecc0e2e1f70837')
        check('password', 'ATHENA.MIT.EDUraeburn', 2, 16,
              '01dbee7f4a9e243e988b62c73cda935d')
        check('password', 'ATHENA.MIT.EDUraeburn', 2, 32,
              '01dbee7f4a9e243e988b62c73cda935da05378b93244ec8f48a99e61ad799d86')
        check('password', 'ATHENA.MIT.EDUraeburn', 1200, 32,
              '5c08eb61fdf71e4e4ec3cf6ba1f5512ba7e52ddbc5e5142f708a31e2e62b1e13')
        check('X' * 64, 'pass phrase equals block size', 1200, 32,
              '139c30c0966bc32ba55fdbf212530ac9c5ec59f1a452f5cc9ad940fea0598ed1')
        check('X' * 65, 'pass phrase exceeds block size', 1200, 32,
              '9ccad6d468770cd51b10e6a68721be611a8b4d282601db3b36be9246915ec82a')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SecurityTestCase))
    return suite
