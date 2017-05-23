#!/usr/bin/env bash
# example use:
#   bash bin/cleanup.sh

isort -rc wizard_builder/
autopep8 --in-place --recursive --aggressive --aggressive wizard_builder/ --max-line-length 119 --exclude="*/migrations/*"
flake8 wizard_builder/
