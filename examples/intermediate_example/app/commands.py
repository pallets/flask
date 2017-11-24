from flask_script import Command
import code

class REPL(Command):
    "runs the shell"

    def run(self):
        code.interact(local=locals())

