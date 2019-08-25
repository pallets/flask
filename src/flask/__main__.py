# -*- coding: utf-8 -*-
"""
    flask.__main__
    ~~~~~~~~~~~~~~

    Alias for flask.run for the command line.

    :copyright: 2010 Pallets
    :license: BSD-3-Clause
"""

if __name__ == "__main__":
    from .cli import main

    main(as_module=True)
