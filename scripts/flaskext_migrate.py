# CASE 1 - from flask.ext.foo import bam --> from flask_foo import bam
# CASE 2 - from flask.ext import foo --> import flask_foo as foo

from redbaron import RedBaron
import sys


with open("test.py", "r") as source_code:
    red = RedBaron(source_code.read())

print red.dumps()

# with open("code.py", "w") as source_code:
#     source_code.write(red.dumps())
