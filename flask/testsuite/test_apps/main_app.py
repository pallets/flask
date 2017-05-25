import os
import flask

# Test Flask initialization with main module.
app = flask.Flask('__main__', instance_path=os.path.join(os.path.abspath(os.path.dirname('__main__')),'instance'))
