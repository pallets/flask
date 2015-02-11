from flask.ext.foo import \
    bam, \
    crackle

from flask.ext import foo

from flask.ext.foo import (bam,
                           a,
                           b
)


from flask.ext import foo

import sys

def migrate(old_file):
    new_file = open("temp.py", "w")
    for line in old_file:
        if line[0, 15] is "from flask.ext":
            if line[15] == '.':
                import_statement = line[16::].split(' ')
                extension = import_statement[0]
                line = line. replace("flask.ext." + extension,
                                     "flask_" + extension)
            else:
                pass

        new_file.write(line)


if __name__ == "__main__":
    old_file = open(sys.arv[1])
