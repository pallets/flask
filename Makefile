.PHONY: all install-dev test coverage cov test-all tox docs audit release clean-pyc upload-docs ebook

all: test

install-dev:
	pip install -q -e .[dev]

test: clean-pyc install-dev
	pytest

coverage: clean-pyc install-dev
	pip install -q -e .[test]
	coverage run -m pytest
	coverage report
	coverage html

cov: coverage

test-all: install-dev
	tox

tox: test-all

docs: clean-pyc install-dev
	$(MAKE) -C docs html

audit:
	python setup.py audit

release:
	python scripts/make-release.py

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

upload-docs:
	$(MAKE) -C docs html dirhtml latex epub
	$(MAKE) -C docs/_build/latex all-pdf
	cd docs/_build/; mv html flask-docs; zip -r flask-docs.zip flask-docs; mv flask-docs html
	rsync -a docs/_build/dirhtml/ flow.srv.pocoo.org:/srv/websites/flask.pocoo.org/docs/
	rsync -a docs/_build/latex/Flask.pdf flow.srv.pocoo.org:/srv/websites/flask.pocoo.org/docs/flask-docs.pdf
	rsync -a docs/_build/flask-docs.zip flow.srv.pocoo.org:/srv/websites/flask.pocoo.org/docs/flask-docs.zip
	rsync -a docs/_build/epub/Flask.epub flow.srv.pocoo.org:/srv/websites/flask.pocoo.org/docs/flask-docs.epub

# ebook-convert docs: http://manual.calibre-ebook.com/cli/ebook-convert.html
ebook:
	@echo 'Using .epub from `make upload-docs` to create .mobi.'
	@echo 'Command `ebook-covert` is provided by calibre package.'
	@echo 'Requires X-forwarding for Qt features used in conversion (ssh -X).'
	@echo 'Do not mind "Invalid value for ..." CSS errors if .mobi renders.'
	ssh -X pocoo.org ebook-convert /var/www/flask.pocoo.org/docs/flask-docs.epub /var/www/flask.pocoo.org/docs/flask-docs.mobi --cover http://flask.pocoo.org/docs/_images/logo-full.png --authors 'Armin Ronacher'
