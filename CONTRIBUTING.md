# Contributing to callisto-core

Thank you so much for considering contributing to callisto-core. We couldn't do the work that we do as a small tech nonprofit without the help of wonderful volunteers like yourself.

These guidelines are a work in progress and will be updated as we refine our contributing process. If you have any questions, don't hesitate to ask.

We're working on moving relevant issues from our private bug tracker over to the [GitHub issues](https://github.com/SexualHealthInnovations/callisto-core/issues) on this repo. Beyond the features and bugs listed there, we would very much welcome contributions to improve our non-existent documentation, and are happy to provide extensive support!

#### Your first contribution
Working on your first open source contribution? We are so excited to have you! You can learn how to make a pull request from this free series [How to Contribute to an Open Source Project on GitHub](https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github)!

#### How to submit
We need all contributors to sign our [volunteer agreement](https://github.com/SexualHealthInnovations/callisto-core/blob/master/shi-volunteer-agreement.pdf) (PDF) in order to accept contributions. Signed agreements can be submitted to tech@sexualhealthinnovations.org. We can take fixes to documentation without a signed agreement.

#### How to run tests
````
git clone git@github.com:SexualHealthInnovations/callisto-core.git # first time only
cd callisto-core
pip install virtualenv # first time only
virtualenv venv # localize your dependencies
source venv/bin/activate
pip install -r requirements-test.txt # requires postgres to be installed (brew install postgres)
make test # run tests quickly with the default Python. Prefer this over running ``python runtests.py`` directly.
deactivate # exit virtualenv
  ````

#### How to report a bug

**If you find a security vulnerability, do NOT open a GitHub issue.** Email tech@sexualhealthinnovations.org instead. We will respond as soon as possible.

Other bugs or feature requests can be submitted as [GitHub issues](https://github.com/SexualHealthInnovations/callisto-core/issues) on this repo.

#### Other questions

Contact us at tech@sexualhealthinnovations.org.
