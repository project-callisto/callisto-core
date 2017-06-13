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

help:
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

clean: ## clean the local files for a release
	make clean-build
	make clean-pyc

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc: ## remove Python file artifacts
	find callisto -name '*.pyc' -exec rm -f {} +
	find callisto -name '*.pyo' -exec rm -f {} +
	find callisto -name '*~' -exec rm -f {} +
	find callisto -type d -name "__pycache__" -exec rm -rf {} +

clean-lint: ## cleanup / display issues with isort and pep8
	isort -rc callisto/
	autopep8 --in-place --recursive --aggressive --aggressive callisto/ --max-line-length 119 --exclude="*/migrations/*"

test-lint: ## check style with pep8 and isort
	flake8 callisto/
	isort --check-only --diff --quiet -rc callisto/

test-suite: ## run the unit and integration tests
	pytest -v

test: ## run the linters and the test suite
	make test-lint
	make test-suite

release: ## package and upload a release
	make clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload
	python setup.py tag

sdist: ## package
	make clean
	python setup.py sdist
	ls -l dist
