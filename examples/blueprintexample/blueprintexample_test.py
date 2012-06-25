# -*- coding: utf-8 -*-
"""
    Blueprint Example Tests
    ~~~~~~~~~~~~~~

    Tests the Blueprint example app
"""
import blueprintexample
import unittest


class BlueprintExampleTestCase(unittest.TestCase):

    def setUp(self):
        self.app = blueprintexample.app.test_client()
        
    def test_urls(self):
        r = self.app.get('/')
        self.assertEquals(r.status_code, 200)
        
        r = self.app.get('/hello')
        self.assertEquals(r.status_code, 200)
        
        r = self.app.get('/world')
        self.assertEquals(r.status_code, 200)
        
        #second blueprint instance
        r = self.app.get('/pages/hello')
        self.assertEquals(r.status_code, 200)
        
        r = self.app.get('/pages/world')
        self.assertEquals(r.status_code, 200)
        
        
if __name__ == '__main__':
    unittest.main()
