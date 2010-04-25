.PHONY: clean-pyc test

all: clean-pyc test

test:
	python tests/flask_tests.py

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

upload-docs:
	$(MAKE) -C docs dirhtml latex
	$(MAKE) -C docs/_build/latex all-pdf
	scp -r docs/_build/dirhtml/* pocoo.org:/var/www/flask.pocoo.org/docs/
	scp -r docs/_build/latex/Flask.pdf pocoo.org:/var/www/flask.pocoo.org/docs/flask-docs.pdf
