# Developement Guide

## Installation

Run the commands in all these sections, in order

### System Dependencies (OSX)

Install the following

- homebrew
- git
- pyenv
- postgres

via

    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    brew update
    brew upgrade
    brew install git, pyenv, postgres

### System Dependencies (Linux)

The requirements are the same, you will just want to swap out homebrew for apt-get or similar

### Local Environment Setup

    git clone git@github.com:project-callisto/callisto-core.git # first time only
    cd callisto-core
    export PYTHON_VERSION=`cat runtime.txt | sed -e 's/python-//'`
    pyenv install $PYTHON_VERSION -s
    pyenv local $PYTHON_VERSION
    python -m venv .venv
    source .venv/bin/activate

### Local Environment Setup Part 2

    pip install -r callisto_core/requirements/dev.txt --upgrade
    make app-setup

## Running

The tests

    make test

The demo app

    python manage.py runserver

Your local demo application should match the live version present at https://callisto-core.herokuapp.com/
