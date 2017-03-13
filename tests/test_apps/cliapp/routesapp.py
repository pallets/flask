from __future__ import absolute_import, print_function

from flask import Flask


noroute_app = Flask('noroute app')
simpleroute_app = Flask('simpleroute app')
only_POST_route_app = Flask('GET route app')


@simpleroute_app.route('/simpleroute')
def simple():
    pass


@only_POST_route_app.route('/only-post', methods=['POST'])
def only_post():
    pass
