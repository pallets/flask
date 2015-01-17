# EASY-INSTALL-DEV-SCRIPT: %(spec)r,%(script_name)r
__requires__ = """%(spec)r"""
import sys
from pkg_resources import require
require("""%(spec)r""")
del require
__file__ = """%(dev_path)r"""
if sys.version_info < (3, 0):
    execfile(__file__)
else:
    exec(compile(open(__file__).read(), __file__, 'exec'))
