import os
import flask
here = os.path.abspath(os.path.dirname(__file__))
app = flask.Flask(__name__, instance_path=os.path.join(os.path.abspath(
                os.path.dirname(os.path.dirname(__file__))),'instance')
               )
