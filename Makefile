.PHONY: clean-pyc test

all: clean-pyc test

test:
	python tests/flask_tests.py

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
