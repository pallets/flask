from lib2to3.fixer_base import BaseFix
from lib2to3.fixer_util import Name, syms


class FixExtImport(BaseFix):

    PATTERN = "fixnode='oldname'"

    def transform(self, node, results):
        fixnode = results['fixnode']
        fixnode.replace(Name('newname', prefix=fixnode.prefix))

        if node.type == syms.import_from and \
                getattr(results['imp'], 'value', None) == 'flask.ext':
            return 0
            # TODO: Case 2


# CASE 1 - from flask.ext.foo import bam --> from flask_foo import bam
# CASE 2 - from flask.ext import foo --> import flask_foo as foo
