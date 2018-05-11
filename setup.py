#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import re
from collections import OrderedDict

from setuptools import setup

with io.open('README.rst', 'rt', encoding='utf8') as f:
    readme = f.read()

with io.open('flask/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)

setup(
    name='Flask',
    version=version,
    url='https://www.palletsprojects.com/p/flask/',
    project_urls=OrderedDict((
        ('Documentation', 'http://flask.pocoo.org/docs/'),
        ('Code', 'https://github.com/pallets/flask'),
        ('Issue tracker', 'https://github.com/pallets/flask/issues'),
    )),
    license='BSD',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    maintainer='Pallets team',
    maintainer_email='contact@palletsprojects.com',
    description='A simple framework for building complex web applications.',
    long_description=readme,
    packages=['flask', 'flask.json'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    install_requires=[
        'Werkzeug>=0.14',
        'Jinja2>=2.10',
        'itsdangerous>=0.24',
        'click>=5.1',
    ],
    extras_require={
        'dotenv': ['python-dotenv'],
        'dev': [
            'pytest>=3',
            'coverage',
            'tox',
            'sphinx',
            'pallets-sphinx-themes',
            'sphinxcontrib-log-cabinet',
        ],
        'docs': [
            'sphinx',
            'pallets-sphinx-themes',
            'sphinxcontrib-log-cabinet',
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points={
        'console_scripts': [
            'flask = flask.cli:main',
        ],
    },
)
