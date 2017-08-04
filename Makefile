.PHONY: clean-pyc clean-build docs help
.DEFAULT_GOAL := help
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"
VERSION := $(shell cat wizard_builder/version.txt)

help:
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

clean: ## clean the repo in preparation for release
	make clean-build
	make clean-pyc

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc: ## remove Python file artifacts
	find wizard_builder -name '*.pyc' -exec rm -f {} +
	find wizard_builder -name '*.pyo' -exec rm -f {} +
	find wizard_builder -name '*~' -exec rm -f {} +
	find wizard_builder -type d -name "__pycache__" -exec rm -rf {} +

clean-lint: ## run the cleanup functions for the linters
	isort -rc wizard_builder/
	autopep8 --in-place --recursive --aggressive --aggressive wizard_builder/ --max-line-length 119 --exclude="*/migrations/*, */tests/*"
	make test-lint

test-lint: ## lint with isort and flake8
	isort --check-only --diff --quiet -rc wizard_builder/
	flake8 wizard_builder/ --exclude="*/migrations/*, */tests/*"

test-suite: ## run the unit and intregration tests
	pytest -v

test-fast: ## runs the test suite, with fast failures and a re-used database
	pytest -v -l -s --maxfail=1 --ff --reuse-db

test: ## run both the test suite and the linters
	make test-lint
	make test-suite

test-all: ## run tests on every Python version with tox
	tox

release: clean ## package and upload a release
	python setup.py sdist upload
	python setup.py bdist_wheel upload
	git tag -a $(VERSION) -m 'version $(VERSION)'
	git push --tags
	git push

sdist: clean ## package
	python setup.py sdist
	ls -l dist

django-release: ## heroku build release command
	python manage.py migrate --noinput --database default
	python manage.py create_admins
