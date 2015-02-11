# CASE 1 - from flask.ext.foo import bam --> from flask_foo import bam
# CASE 2 - from flask.ext import foo --> import flask_foo as foo

from redbaron import RedBaron
import sys


def read_source(input_file):
    with open(input_file, "r") as source_code:
        red = RedBaron(source_code.read())
    return red


def write_source(red, input_file):
    with open(input_file, "w") as source_code:
        source_code.write(red.dumps())


def fix_imports(red):
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


if __name__ == "__main__":
    input_file = sys.argv[1]
    ast = read_source(input_file)
    new_ast = fix_imports(ast)
    write_source(new_ast, input_file)
