# Script which modifies source code away from the deprecated "flask.ext"
# format. Does not yet fully support imports in the style:
#
# "import flask.ext.foo"
#
# these are converted to "import flask_foo" in the
# main import statement, but does not handle function calls in the source.
#
# Run in the terminal by typing: `python flaskext_migrate.py <source_file.py>`
#
# Author: Keyan Pishdadian 2015

from redbaron import RedBaron
import sys


def read_source(input_file):
    """Parses the input_file into a RedBaron FST."""
    with open(input_file, "r") as source_code:
        red = RedBaron(source_code.read())
    return red


def write_source(red, input_file):
    """Overwrites the input_file once the FST has been modified."""
    with open(input_file, "w") as source_code:
        source_code.write(red.dumps())


def fix_imports(red):
    """Wrapper which fixes "from" style imports and then "import" style."""
    red = fix_standard_imports(red)
    red = fix_from_imports(red)
    return red


def fix_from_imports(red):
    """
    Converts "from" style imports to not use "flask.ext".

    Handles:
    Case 1: from flask.ext.foo import bam --> from flask_foo import bam
    Case 2: from flask.ext import foo --> import flask_foo as foo
    """
    from_imports = red.find_all("FromImport")
    for x in range(len(from_imports)):
        values = from_imports[x].value
        if (values[0].value == 'flask') and (values[1].value == 'ext'):
            # Case 1
            if len(from_imports[x].value) == 3:
                package = values[2].value
                modules = from_imports[x].modules()
                r = "{}," * len(modules)
                from_imports[x].replace("from flask_%s import %s"
                                        % (package, r.format(*modules)[:-1]))
            # Case 2
            else:
                module = from_imports[x].modules()[0]
                from_imports[x].replace("import flask_%s as %s"
                                        % (module, module))
    return red


def fix_standard_imports(red):
    """
    Handles import modification in the form:
    import flask.ext.foo" --> import flask_foo

    Does not modify function calls elsewhere in the source outside of the
    original import statement.
    """
    imports = red.find_all("ImportNode")
    for x in range(len(imports)):
        values = imports[x].value
        try:
            if (values[x].value[0].value == 'flask' and
            values[x].value[1].value == 'ext'):
                package = values[x].value[2].value
                imports[x].replace("import flask_%s" % package)
        except IndexError:
            pass

    return red


def fix(input_file):
    ast = read_source(input_file)
    new_ast = fix_imports(ast)
    write_source(new_ast, input_file)

if __name__ == "__main__":
    input_file = sys.argv[1]
    fix(input_file)
