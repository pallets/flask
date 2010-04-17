.PHONY: clean-pyc test

all: clean-pyc test

test:
	python tests/flask_tests.py

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

upload-website:
	scp -r website/* pocoo.org:/var/www/flask.pocoo.org/

upload-docs:
	$(MAKE) -C docs html && scp -r docs/_build/html/* pocoo.org:/var/www/flask.pocoo.org/docs/
