import os

from src.notifier.emailsender.template import StonTemplate
from aws_lambda_powertools import Logger
import datetime
import re

logger = Logger()

email_validator = "([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"


def body_template_builder():
    """
    Function useful to return body template.

    :return:
    """
    template = StonTemplate()
    return template.get_template("body_template.html") if template else None


def subject_template_builder():
    """
        Function useful to return body template.

        :return:
        """
    template = StonTemplate()
    return template.get_template("subject_template.html") if template else None


def ses_request_builder(user: dict, ses) -> None:
    """
    Send email using AWS SES

    :param user:
    :param ses:
    :return:
    """
    subject_template = subject_template_builder()
    body_template = body_template_builder()
    context = {}
    for k, v in user.items():
        context = {
            "user": {
                "username": k,
                "expired_days": v.get('password_days_age'),
                "last_changed": v.get('password_last_changed'),
                "password_days_age": v.get('password_days_age'),
                "email": v.get('email'),
                "account": v.get('account')
            },
            "email": {
                "subject": f"{k} la tua password è scaduta!"
            }
        }
    body_data = body_template.render(context=context)
    subject_data = subject_template.render(context=context)
    subject = {'Data': subject_data, 'Charset': 'utf-8'}
    body = {'Html': {'Data': body_data, 'Charset': 'utf-8'}}
    logger.info(f"Sending email ... to: {str(context.get('user').get('email'))}")
    ses.send_email(Source=os.getenv('EMAIL_FROM', 'noreply@noreply.com'), Destination={'ToAddresses': [context.get('user').get('email')]},
                       Message={'Subject': subject, 'Body': body})


def users_builder(credential, iam) -> list:
    """
    Build an object useful to inject as context for email templates.

    :param iam:
    :param credential:
    :return:
    """
    wake_up_users = []
    users = credential.split('\n')[1:]
    for user in users:
        user_info = user.split(',')
        if 'true' == user_info[3]:
            password_age = 0
            try:
                password_last_changed = datetime.datetime.fromisoformat(user_info[5])
                password_age = datetime.datetime.now() - password_last_changed.replace(tzinfo=None)
            except ValueError:
                logger.info(f"The current user {user_info[0]} has not password enabled")
            if 'true' == user_info[3] and password_age.days >= int(os.getenv("OLD_AGE_PASSWORD", 75)):
                response = iam.list_user_tags(UserName=user_info[0])
                tags: dict = response.get('Tags')
                if len(tags) > 0:
                    for tag in tags:
                        key = tag.get('Key')
                        value = tag.get('Value')
                        if key == 'email' and re.fullmatch(email_validator, value):
                            email = value
                            wake_up_users.append({user_info[0]: {
                                'username': user_info[0],
                                'password_last_changed': user_info[5],
                                'password_days_age': password_age.days,
                                'email': email,
                                'account': str(user_info[1]).split(":")[4]
                            }})
                            break
                        else:
                            logger.info(
                                f"For user {user_info[0]} there isn't configured email tag or email value is not valid")
    logger.info(f"The users to wakeup are: {''.join(map(str, wake_up_users))}")
    return wake_up_users


def report_generator(iam):
    """
    To get credentials report, it must exist before.

    :param iam:
    :return:
    """
    res = iam.generate_credential_report()
    return res.get('State')
