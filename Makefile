.PHONY: all install-dev test coverage cov test-all tox docs audit release clean-pyc upload-docs ebook

all: test

install-dev:
	pip install -q -e .[dev]

test: clean-pyc install-dev
	pytest

coverage: clean-pyc install-dev
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
