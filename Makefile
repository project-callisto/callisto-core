.DEFAULT_GOAL := help

help:
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

clean:
	make clean-build
	make clean-lint

clean-build: ## clean the local files for a release
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info
	rm -rf *.sqlite3
	find callisto_core -name '*.pyc' -exec rm -f {} +
	find callisto_core -name '*.pyo' -exec rm -f {} +
	find callisto_core -name '*~' -exec rm -f {} +
	find callisto_core -type d -name "__pycache__" -exec rm -rf {} +

clean-lint: ## cleanup / display issues with isort and pep8
	autopep8 callisto_core/ -raai
	isort -rc callisto_core/
	make test-lint

test-lint: ## check style with pep8 and isort
	flake8 callisto_core/
	isort --check-only --diff --quiet -rc callisto_core/

test-suite: ## run the unit and integration tests
	pytest -v

test-fast: ## runs the test suite, with fast failures and a re-used database
	pytest -v -l -s --maxfail=1 --ff --reuse-db

test: ## run the linters and the test suite
	make test-lint
	make test-suite

release: ## package and upload a release
	make clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload
	python setup.py tag
	make clean

pip-install:
	pip install -r callisto_core/requirements/dev.txt --upgrade

app-setup: ## setup the test application environment
	- python manage.py flush --noinput
	python manage.py migrate --noinput --database default
	python manage.py create_admins
	python manage.py setup_sites
	python manage.py loaddata wizard_builder_data
	python manage.py loaddata callisto_core_notification_data
