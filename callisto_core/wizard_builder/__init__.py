import os

__version_path = os.path.join(
    os.path.abspath(
        os.path.dirname(__file__)),
    'version.txt',
)
with open(__version_path, 'r') as f:
    __version__ = f.read()

default_app_config = 'wizard_builder.apps.WizardBuilderConfig'
