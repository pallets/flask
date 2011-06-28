.PHONY: clean-pyc ext-test test upload-docs docs audit

all: clean-pyc test

test:
	python setup.py test

audit:
	python setup.py audit

release:
	python scripts/make-release.py

tox-test:
	PYTHONDONTWRITEBYTECODE= tox

ext-test:
	python tests/flaskext_test.py --browse

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

upload-docs:
	$(MAKE) -C docs html dirhtml latex
	$(MAKE) -C docs/_build/latex all-pdf
	cd docs/_build/; mv html flask-docs; zip -r flask-docs.zip flask-docs; mv flask-docs html
	rsync -a docs/_build/dirhtml/ pocoo.org:/var/www/flask.pocoo.org/docs/
	rsync -a docs/_build/latex/Flask.pdf pocoo.org:/var/www/flask.pocoo.org/docs/flask-docs.pdf
	rsync -a docs/_build/flask-docs.zip pocoo.org:/var/www/flask.pocoo.org/docs/flask-docs.zip

docs:
	$(MAKE) -C docs html
