import io

from setuptools import find_packages
from setuptools import setup

with io.open("README.rst", "rt", encoding="utf8") as f:
    readme = f.read()

setup(
    name="js_example",
    version="1.0.0",
    url="http://flask.pocoo.org/docs/patterns/jquery/",
    license="BSD",
    maintainer="Pallets team",
    maintainer_email="contact@palletsprojects.com",
    description="Demonstrates making Ajax requests to Flask.",
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["flask"],
    extras_require={"test": ["pytest", "coverage", "blinker"]},
)
