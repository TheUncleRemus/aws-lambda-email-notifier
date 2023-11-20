import boto3
import logging
import botocore.exceptions as aws_exception
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from src.notifier.emailsender import builder

logger = Logger()

__msg_no_credentials_error = "There aren't any credentials"
__msg_return_error_case = "There was an error. The emails was not sent"


@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> str:
    """
    AWS Lambda handler. This function return a code status eq to 0
    if the email has been sent, a code status !=0 else.

    :param event:
    :param context:
    :return:
    """
    request = APIGatewayProxyEvent(event)
    logger.set_correlation_id(request.request_context.get('function_request_id'))
    logger.info(msg=f"Correlation ID => {logger.get_correlation_id()}")
    try:
        logger.info(msg="Setup IAM Client")
        iam = boto3.client("iam")
        logger.info(msg="Setup SES Client")
        ses = boto3.client("ses")
        # the default MaxItems is 100. The pagination is not necessary
        status = builder.report_generator(iam)
        while 'COMPLETE' != status:
            status = builder.report_generator(iam)
        iam_report = iam.get_credential_report()
        if iam_report is None or len(iam_report) == 0:
            raise aws_exception.BotoCoreError(msg=("%s" % __msg_no_credentials_error))
        encoded_csv = iam_report.get("Content")
        if encoded_csv is None:
            raise aws_exception.BotoCoreError(msg=("%s" % __msg_no_credentials_error))
        credentials = encoded_csv.decode('utf-8')
        users_to_notify = builder.users_builder(credentials, iam)
        logger.info(msg=f" users to notify: {len(users_to_notify)}")
        for user in users_to_notify:
            logger.info(msg=f"Send email to: {user.get(list(user.keys())[0]).get('email')}")
            builder.ses_request_builder(user, ses)
        return f"Has been sent the email for follow users {[','.join(user.keys()) for user in users_to_notify]}"
    except aws_exception.ClientError:
        logger.error(msg="Error during the IAM client creation", exc_info=True)
        return "%s" % __msg_return_error_case
    except aws_exception.BotoCoreError as e:
        logger.error(msg=f"{str(e)}", exc_info=True)
        return "%s" % __msg_return_error_case
    except Exception as e:
        logger.error(msg=f"{str(e)}", exc_info=True)
        return "%s" % __msg_return_error_case


