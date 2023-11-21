# aws-lambda-email-notifier

This is a lambda function useful to sends an email to all AWS users that has expired the password.

## ToC

<!-- TOC -->
* [aws-lambda-email-notifier](#aws-lambda-email-notifier)
  * [ToC](#toc)
  * [project layout](#project-layout)
  * [environment variables](#environment-variables)
  * [serverless framework](#serverless-framework)
    * [plugins](#plugins)
      * [howto install the plugins](#howto-install-the-plugins)
  * [test](#test)
  * [howto deploy with serverless](#howto-deploy-with-serverless)
<!-- TOC -->

## project layout
The project structure is based on a canonical _src layout_ with pyproject.tml as file 
descriptor to indicate the build subsystem and pre requirements useful to python _build_
module.

The project use both "lifecycle" files _pyproject.toml_ and _setup.cfg_ because the
compliance to setuptools is less entropic using _setup.cfg_ instead of _pyproject.toml_.
For this reason the pyproject.tml define just subsystem build section.

## environment variables

The lambda use the `aws_lambda_powertools`, and then the project needs of the below environment variables:

|name                       |value                |type|mandatory                                |
|---------------------------|---------------------|----|-----------------------------------------|
|POWERTOOLS_LOGGER_LOG_EVENT|True                 |bool|if not in production                     |
|POWERTOOLS_SERVICE_NAME    |<service_custom_name>|str |usefult to configure the aws power logger|
|LOG_LEVEL                  |True                 |bool|useful to configure the basic logger     |
|OLD_AGE_PASSWORD           |75                   |int |useful to set a old age of password      |

## serverless framework

[Serverless](https://www.serverless.com/) is a framework useful to configure, pack and deploy AWS lambda function.
This project use this framework.
The meaningful snippets of `serverless.yaml` file, are (dot.notation):

- `provider.profile`
- `provider.region`
- `provider.iam`
- `custom.pythonRequirements`
- `function.environment.EMAIL_FROM`

| section.attribute               | which means                                                                                                                                        |
|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------| 
| provider.profile                | represents the key of your aws profile (into $HOME/.aws/config. Read the [plugin section](#plugins))                                               |
| provider.region                 | represents the region where your aws profile has been configured                                                                                   |
| provider.iam                    | represents the section of IAM permission. List the policies needs to the current lambda to works fine                                              |
| custom.pythonRequirements       | represents the python rewuirements layer. Read the [plugin section](#plugins)                                                                      |
| function.environment.EMAIL_FROM | represents the value of your FROM email adressed. Note: the emails will be send from **aws ses**, for this reason you need to configure ses before | 

### plugins

The serverless plugin installed are:

- `serverless-python-requirements`
- `serverless-better-credentials`

The first plugin is useful to install python requirements. The second one is useful to use aws local $HOME/.aws/_config_
file instead of local .aws/_credentials_.

#### howto install the plugins

```bash
serverless plugin install -n serverless-python-requirements
```

```bash
serverless plugin install -n serverless-better-credentials
```
## test

Under the `test` package you can find some "unittest", but if you want to run these tests you need to configure the environment
variable `AWS_PROFILE`, because the test calls the aws apis (like an "integration" test).

## howto deploy with serverless

First of all you can install serverless framework. To do this you can reach the serverless documentation from 
[serverless framework](#serverless-framework).

```shell
git clone https://github.com/TheUncleRemus/aws-lambda-email-notifier.git
```

```shell
cd aws-lambda-email-notifier/
```

```shell
serverless deploy
```