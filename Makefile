VERSION := $(shell cat wizard_builder/version.txt)
DATA_FILE := wizard_builder/fixtures/wizard_builder_data.json

help:
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

clean:
	make clean-lint
	make clean-build

clean-lint: ## run the cleanup functions for the linters
	autopep8 wizard_builder/ -raai
	isort -rc wizard_builder/
	make test-lint

test-lint: ## lint with isort and flake8
	flake8 wizard_builder/
	isort --check-only --diff --quiet -rc wizard_builder/

test-fast:
	pytest -vlsx --ff --reuse-db --ignore=wizard_builder/tests/test_frontend.py --ignore=wizard_builder/tests/test_admin.py --ignore=wizard_builder/tests/test_migrations.py

test-local-suite:
	python manage.py check
	pytest -v --ignore wizard_builder/tests/test_frontend.py --ignore wizard_builder/tests/test_admin.py
	pytest -v wizard_builder/tests/test_frontend.py
	pytest -v wizard_builder/tests/test_admin.py

install-pip:
	pip install -r requirements/test.txt --upgrade

install-osx:
	make install-pip
	brew install git pyenv postgres chromedriver

test-callisto-core:
	pip install callisto-core --upgrade
	pip show callisto-core |\
		grep 'Location' |\
		sed 's/Location: \(.*\)/\1\/callisto_core\/requirements\/test.txt/' |\
		xargs -t pip install --upgrade -r
	pip uninstall -y django-wizard-builder
	pip install -e .
	pip show callisto-core |\
		grep 'Location' |\
		sed 's/Location: \(.*\)/\1\/callisto_core\/tests/' |\
		xargs -t pytest -v --ds=wizard_builder.tests.callisto_core_settings

test-all:
	make test-lint
	make test-local-suite
	make test-callisto-core

clean-build: ## clean the repo in preparation for release
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info
	rm -rf wizard_builder/tests/screendumps/
	rm -rf wizard_builder/tests/staticfiles/
	find wizard_builder -name '*.pyc' -exec rm -f {} +
	find wizard_builder -name '*.pyo' -exec rm -f {} +
	find wizard_builder -name '*~' -exec rm -f {} +
	find wizard_builder -type d -name "__pycache__" -exec rm -rf {} +

release: ## package and upload a release
	make clean-build
	python setup.py sdist upload
	python setup.py bdist_wheel upload
	git tag -a $(VERSION) -m 'version $(VERSION)'
	git push --tags
	git push
	make clean-build

app-setup: ## setup the test application environment
	- rm wizard_builder_test_app.sqlite3
	- python manage.py flush --noinput
	python manage.py migrate --noinput
	python manage.py create_admins
	python manage.py setup_sites
	make load-fixture

shell: ## manage.py shell_plus with dev settings
	DJANGO_SETTINGS_MODULE='wizard_builder.tests.test_app.dev_settings' python manage.py shell_plus

load-fixture: ## load fixture from file
	python manage.py loaddata $(DATA_FILE)

update-fixture: ## update fixture with migrations added on the local branch
	git checkout master
	- rm wizard_builder_test_app.sqlite3
	- python manage.py migrate
	- python manage.py loaddata $(DATA_FILE) -i
	git checkout @{-1}
	python manage.py migrate
	python manage.py dumpdata wizard_builder -o $(DATA_FILE)
	npx json -f $(DATA_FILE) -I
