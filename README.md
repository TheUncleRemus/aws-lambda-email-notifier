# e0-py-lambda-ses-notifier

This is a lambda function useful to sends an email to all AWS users that has expired the password.

## layout
The project structure is based on a canonical _src layout_ with pyproject.tml as file 
descriptor to indicate the build subsystem and pre requirements useful to python _build_
module.

The project use both "lifecycle" files _pyproject.toml_ and _setup.cfg_ because the
compliance to setuptools is less entropic using _setup.cfg_ instead of _pyproject.toml_.
For this reason the pyproject.tml define just subsystem build section.

## environment variables

The lambda use the aws-powertools, and then:

- set env var **POWERTOOLS_LOGGER_LOG_EVENT** if not in production env
- set env **POWERTOOLS_SERVICE_NAME** always
- set **LOG_LEVEL** based on environment

## serverless

### plugins

The first plugin is useful to install python requirements. The second one is useful to use aws local 
.aws/_config_ file instead of local .aws/_credentials_ 

- serverless plugin install -n serverless-python-requirements
- serverless plugin install -n serverless-better-credentials
