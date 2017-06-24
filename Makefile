.PHONY: clean-pyc clean-build help
.DEFAULT_GOAL := help

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
	find callisto-core -name '*.pyc' -exec rm -f {} +
	find callisto-core -name '*.pyo' -exec rm -f {} +
	find callisto-core -name '*~' -exec rm -f {} +
	find callisto-core -type d -name "__pycache__" -exec rm -rf {} +

clean-lint: ## cleanup / display issues with isort and pep8
	isort -rc callisto-core/
	autopep8 --in-place --recursive --aggressive --aggressive callisto-core/ --max-line-length 119 --exclude="*/migrations/*"

test-lint: ## check style with pep8 and isort
	flake8 callisto-core/
	isort --check-only --diff --quiet -rc callisto-core/

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
