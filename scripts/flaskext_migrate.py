# Script which modifies source code away from the deprecated "flask.ext"
# format.
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
    for x, node in enumerate(from_imports):
        values = node.value
        if len(values) < 2:
            continue
        if (values[0].value == 'flask') and (values[1].value == 'ext'):
            # Case 1
            if len(node.value) == 3:
                package = values[2].value
                modules = node.modules()
                module_string = _get_modules(modules)
                if len(modules) > 1:
                    node.replace("from flask_%s import %s"
                                 % (package, module_string))
                else:
                    name = node.names()[0]
                    node.replace("from flask_%s import %s as %s"
                                 % (package, module_string, name))
            # Case 2
            else:
                module = node.modules()[0]
                node.replace("import flask_%s as %s"
                             % (module, module))
    return red


def fix_standard_imports(red):
    """
    Handles import modification in the form:
    import flask.ext.foo" --> import flask_foo
    """
    imports = red.find_all("ImportNode")
    for x, node in enumerate(imports):
        try:
            if (node.value[0].value[0].value == 'flask' and
               node.value[0].value[1].value == 'ext'):
                package = node.value[0].value[2].value
                name = node.names()[0].split('.')[-1]
                if name == package:
                    node.replace("import flask_%s" % (package))
                else:
                    node.replace("import flask_%s as %s" % (package, name))
        except IndexError:
            pass

    return red


def _get_modules(module):
    """
    Takes a list of modules and converts into a string.

    The module list can include parens, this function checks each element in
    the list, if there is a paren then it does not add a comma before the next
    element. Otherwise a comma and space is added. This is to preserve module
    imports which are multi-line and/or occur within parens. While also not
    affecting imports which are not enclosed.
    """
    modules_string = [cur + ', ' if cur.isalnum() and next.isalnum()
                      else cur
                      for (cur, next) in zip(module, module[1:]+[''])]

    return ''.join(modules_string)


def fix_function_calls(red):
    """
    Modifies function calls in the source to reflect import changes.

    Searches the AST for AtomtrailerNodes and replaces them.
    """
    atoms = red.find_all("Atomtrailers")
    for x, node in enumerate(atoms):
        try:
            if (node.value[0].value == 'flask' and
               node.value[1].value == 'ext'):
                params = _form_function_call(node)
                node.replace("flask_%s%s" % (node.value[2], params))
        except IndexError:
            pass

    return red


def _form_function_call(node):
    """
    Reconstructs function call strings when making attribute access calls.
    """
    node_vals = node.value
    output = "."
    for x, param in enumerate(node_vals[3::]):
        if param.dumps()[0] == "(":
            output = output[0:-1] + param.dumps()
            return output
        else:
            output += param.dumps() + "."


def check_user_input():
    """Exits and gives error message if no argument is passed in the shell."""
    if len(sys.argv) < 2:
        sys.exit("No filename was included, please try again.")


def fix_tester(ast):
    """Wrapper which allows for testing when not running from shell."""
    ast = fix_imports(ast)
    ast = fix_function_calls(ast)
    return ast.dumps()


def fix():
    """Wrapper for user argument checking and import fixing."""
    check_user_input()
    input_file = sys.argv[1]
    ast = read_source(input_file)
    ast = fix_imports(ast)
    ast = fix_function_calls(ast)
    write_source(ast, input_file)


if __name__ == "__main__":
    fix()
