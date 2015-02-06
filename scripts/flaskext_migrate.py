# from flask.ext import foo => import flask_foo as foo
# from flask.ext.foo import bam => from flask_foo import bam
# import flask.ext.foo => import flask_foo

import sys


def migrate(old_file):
    new_file = open("temp.py", "w")
    for line in old_file:
        if line[0:14] == "from flask.ext":
            if line[14] == '.':
                import_statement = line[15::].split(' ')
                extension = import_statement[0]
                line = line.replace("flask.ext." + extension,
                                    "flask_" + extension)
            elif line[14] == " ":
                import_statement = line[15::].split(' ')[1]
                import_statement = import_statement.strip('\n')
                line = ("import flask_" +
                        import_statement +
                        " as " +
                        import_statement)

        new_file.write(line)
    new_file.close()

if __name__ == "__main__":
    old_file = open(sys.argv[1])
    migrate(old_file)
