from src.notifier.emailsender.template import StonTemplate
import datetime
import logging
import re

logger = logging.getLogger('ses-notifier')

email_validator = "([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"


def logger_error_builder(e):
    kwargs = e.kwargs
    return kwargs.get('msg') if kwargs is not None else e.fmt


def body_template_builder():
    """
    Function useful to return body template.

    :return:
    """
    template = StonTemplate("../../resources")
    return template.get_template("body_template.html") if template else None


def subject_template_builder():
    """
        Function useful to return body template.

        :return:
        """
    template = StonTemplate("../../resources")
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
                "email": v.get('email')
            },
            "email": {
                "subject": f"{k} la tua password è scaduta!"
            }
        }
    body_data = body_template.render(context=context)
    subject_data = subject_template.render(context=context)
    subject = {'Data': subject_data, 'Charset': 'utf-8'}
    body = {'Html': {'Data': body_data, 'Charset': 'utf-8'}}
    ses.send_email(Source="noreply@noreply.com", Destination={'ToAddresses': [context.get('user').get('email')]},
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
            if 'true' == user_info[3] and password_age.days >= 90:
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
                                'email': email
                            }})
                            break
    return wake_up_users
