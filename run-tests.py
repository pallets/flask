import unittest
from flask.testsuite import BetterLoader
try:
    unittest.main(testLoader=BetterLoader(), defaultTest='suite')
except Exception, e:
    print 'Error: %s' % e
