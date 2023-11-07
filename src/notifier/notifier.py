import boto3
import logging
import botocore.exceptions as aws_exception
from src.notifier.emailsender import builder

logger = logging.Logger('ses-notifier', level=logging.INFO)

__msg_no_credentials_error = "There aren't any credentials"
__msg_return_error_case = "There was an error. The emails was not sent"


def handler(event: dict, context) -> str:
    """
    AWS Lambda handler. This function return a code status eq to 0
    if the email has been sent, a code status !=0 else.

    :param event:
    :param context:
    :return:
    """
    logger.info(f"{event}")
    try:
        logger.info("Setup IAM Client")
        iam = boto3.client("iam")
        logger.info("Setup SES Client")
        ses = boto3.client("ses")
        # the default MaxItems is 100. The pagination is not necessary
        iam_report = iam.get_credential_report()
        if iam_report is None or len(iam_report) == 0:
            raise aws_exception.BotoCoreError(msg=("%s" % __msg_no_credentials_error))
        encoded_csv = iam_report.get("Content")
        if encoded_csv is None:
            raise aws_exception.BotoCoreError(msg=("%s" % __msg_no_credentials_error))
        credentials = encoded_csv.decode('utf-8')
        users_to_notify = builder.users_builder(credentials, iam)
        for user in users_to_notify:
            logger.info(f"Send email to: {user.get(user.keys()[0]).get('email')}")
            builder.ses_request_builder(user, ses)
        return f"Has been sent the email for follow users {[','.join(user.keys()) for user in users_to_notify]}"
    except aws_exception.ClientError:
        logger.error("Error during the IAM client creation", exc_info=True)
        return "%s" % __msg_return_error_case
    except aws_exception.BotoCoreError as e:
        logger.error(builder.logger_error_builder(e))
        return "%s" % __msg_return_error_case
    except Exception as e:
        logger.error(builder.logger_error_builder(e))
        return "%s" % __msg_return_error_case


