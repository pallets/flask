from setuptools import setup

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="Flask",
    install_requires=[
        "Werkzeug>=2.0.0rc4",
        "Jinja2>=3.0.0rc1",
        "itsdangerous>=2.0.0rc2",
        "click>=7.1.2",
    ],
    extras_require={
        "async": ["asgiref>=3.2"],
        "dotenv": ["python-dotenv"],
    },
)
