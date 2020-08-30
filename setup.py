from re import search

from setuptools import setup

with open("src/flask/__init__.py", encoding="UTF-8") as f:
    setup(
    name="Flask",
    version=search(r'__version__ = "(.*?)"', f.read()).group(1),
    install_requires=[
        "Werkzeug>=0.15",
        "Jinja2>=2.10.1",
        "itsdangerous>=0.24",
        "click>=5.1",
    ],
    extras_require={"dotenv": ["python-dotenv"]},
    )

