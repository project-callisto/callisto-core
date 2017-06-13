# Contributing to callisto-core

Thank you so much for considering contributing to callisto-core. We couldn't do the work that we do as a small tech nonprofit without the help of wonderful volunteers like yourself.

These guidelines are a work in progress and will be updated as we refine our contributing process. If you have any questions, don't hesitate to ask.

We are adhering to [Django's coding style
guide](https://docs.djangoproject.com/en/1.9/internals/contributing/writing-code/coding-style/).

We're working on moving relevant issues from our private bug tracker over to the [GitHub issues](https://github.com/SexualHealthInnovations/callisto-core/issues) on this repo. Beyond the features and bugs listed there, we would very much welcome contributions to improve our non-existent documentation, and are happy to provide extensive support!

## Your first contribution
Working on your first open source contribution? We are so excited to have you! You can learn how to make a pull request from this free series [How to Contribute to an Open Source Project on GitHub](https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github)!

## Coding style

We are adhering to [Django's coding style guide](https://docs.djangoproject.com/en/1.10/internals/contributing/writing-code/coding-style/), including a maximum line length of 119 characters. You'll find relevant configuration in [`setup.cfg`](https://github.com/SexualHealthInnovations/callisto-core/blob/master/setup.cfg).

As Django's style guide explains, you can use `isort` to automatically sort imports. Before opening your pull request, sort imports by running `isort -rc .` in the root directory of the project. Travis builds of your PR fail if imports aren't sorted correctly.

Travis (as well as `make test`) will check for violations of [PEP8](https://www.python.org/dev/peps/pep-0008/). To automatically fix many PEP8 issues, run `autopep8 --in-place --recursive --aggressive --aggressive . --max-line-length 119 --exclude="*/migrations/*"` in the root directory of the project.

## How to submit
We need all contributors to sign our [volunteer agreement](https://github.com/SexualHealthInnovations/callisto-core/blob/master/shi-volunteer-agreement.pdf) (PDF) in order to accept contributions. Signed agreements can be submitted to tech@sexualhealthinnovations.org. We can take fixes to documentation without a signed agreement.

#### How to run tests
````
git clone git@github.com:SexualHealthInnovations/callisto-core.git # first time only
cd callisto-core
# install gpg (first time only) see http://blog.ghostinthemachines.com/2015/03/01/how-to-use-gpg-command-line/
pip install virtualenv # first time only
virtualenv venv # localize your dependencies
source venv/bin/activate
pip install -r requirements/dev.txt
make test
deactivate # exit virtualenv
````

#### Supported versions:

Django
- 1.8
- 1.9
- 1.10

Python
- 2.7
- 3.3
- 3.4
- 3.5

To see whether your pull request has passed the build on all of these versions, go to https://travis-ci.org/SexualHealthInnovations/callisto-core/pull_requests and click on your PR title to see all of the builds for your code with the above versions of Django and Python.

## How to report a bug

**If you find a security vulnerability, do NOT open a GitHub issue.** Email tech@sexualhealthinnovations.org instead. We will respond as soon as possible.

Other bugs or feature requests can be submitted as [GitHub issues](https://github.com/SexualHealthInnovations/callisto-core/issues) on this repo.


## Code of conduct

This project adheres to a [code of conduct](https://github.com/SexualHealthInnovations/callisto-core/blob/master/CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to tech@sexualhealthinnovations.org.

## Other questions

Contact us at tech@sexualhealthinnovations.org.
