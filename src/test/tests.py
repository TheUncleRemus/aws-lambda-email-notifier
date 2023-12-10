import os

import boto3
import unittest
import datetime
import re
import json

from src.notifier.emailsender.template import StonTemplate


class LambdaTest(unittest.TestCase):
    """
    Unit Test class suite. This TestCase class is useful for local test.
    """

    __profile = os.getenv('AWS_PROFILE', 'default')

    def __session(self):
        """
        Dummy the session

        :return:
        """
        boto3.setup_default_session(profile_name=self.__profile)

    def __iam(self):
        """
        Dummy the iam client

        :return:
        """
        self.__session()
        session = boto3._get_default_session()
        iam = session.client('iam')
        return iam

    def test_get_users(self):
        """
        This method test the boto3("iam")list_users()

        :return:
        """
        iam = self.__iam()
        users = iam.list_users()
        self.assertTrue(expr=users.get('Users'))

    def test_credentials_report_content(self):
        """
        This method test if the credentials report content exists

        :return:
        """
        iam = self.__iam()
        res = iam.generate_credential_report()
        report = iam.get_credential_report()
        report = report.get('Content')
        self.assertIsNotNone(obj=report) and self.assertTrue(expr='COMPLETE' == res.get('Status'))

    def test_user_credentials(self):
        """
        This method test the correct way to read the credentials report

        :return:
        """
        wake_up_users = []
        with open('../resources/mock/status_reports_test.csv', 'r') as csvfile:
            users = csvfile.readlines()[1:]
            for user in users:
                info = user.split(',')
                if 'true' == info[3]:
                    wake_up_users.append({info[0]: {
                        'username': info[0],
                        'password_last_changed': info[5],
                        'account': str(info[1]).split(":")[4]
                    }})
        self.assertTrue(expr=len(wake_up_users) == 13)

    def test_user_expired_password(self):
        """
        This method test the correct way to check if the user password has expired.

        :return:
        """
        wake_up_users = []
        with open('../resources/mock/status_reports_test.csv', 'r') as csvfile:
            users = csvfile.readlines()[1:]
            for user in users:
                info = user.split(',')
                password_age = 0
                try:
                    password_last_changed = datetime.datetime.fromisoformat(info[5])
                    password_age = datetime.datetime.now() - password_last_changed.replace(tzinfo=None)
                except ValueError:
                    pass
                if 'true' == info[3] and password_age.days >= 90:
                    wake_up_users.append({info[0]: {
                        'username': info[0],
                        'password_last_changed': info[5],
                        'password_days_age': password_age.days
                    }})
        user_to_check = {'fake6': {}}
        self.assertTrue(
            expr=((len(wake_up_users) == 8) and (LambdaTest.__check_if_user_in(wake_up_users, user_to_check))))

    @staticmethod
    def __check_if_user_in(users, member_to_check: dict):
        """
        Check if the user dictionary info is present in list o f users

        :param users:
        :return:
        """
        proposition = []
        [proposition.append(member_to_check.keys() <= user.keys()) for user in users]
        return any(proposition)

    @unittest.skip('S1607 - <test_tagged_email_for_users> strictly depends on the business AWS account')
    def test_tagged_email_for_users(self):
        """
        This method test if the users are tagged with email.

        :return:
        """
        wake_up_users = []
        email_validator = '([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'
        with open('../resources/mock/email_tags_test.csv', 'r') as csvfile:
            users = csvfile.readlines()[2:]
            for user in users:
                info = user.split(',')
                response = self.__iam().list_user_tags(UserName=info[0])
                tags: dict = response.get('Tags')
                if len(tags) > 0:
                    for tag in tags:
                        key = tag.get('Key')
                        value = tag.get('Value')
                        if key == 'email' and re.fullmatch(email_validator, value):
                            email = value
                            wake_up_users.append({info[0]: {
                                'username': info[0],
                                'password_last_changed': info[5],
                                'email': email
                            }})
                            break
        self.assertTrue(expr='frank-zappa@zappadomain.com' == wake_up_users[0].get('frank-zappa').get('email'))

    def test_email_ses_object(self):
        """
        This method verify the content for the body.

        :return:
        """
        users = json.load(open('../resources/mock/wake_up-users.json'))
        template = StonTemplate("../resources")
        subject_template = template.get_template("subject_template.html") if template else None
        body_template = template.get_template("body_template.html") if template else None
        context = {}
        for k, v in users.items():
            context = {
                "user": {
                    "username": k,
                    "expired_days": v.get('password_days_age'),
                    "last_changed": v.get('password_last_changed'),
                    "password_days_age": v.get('password_days_age'),
                    "account": v.get("account")
                },
                "email": {
                    "subject": f"{k} la tua password è scaduta!"
                }
            }
        body_data = body_template.render(context=context)
        subject_data = subject_template.render(context=context)
        subject = {'Data': subject_data, 'Charset': 'utf-8'}        #TODO: use also in assert condition
        body = {'Html': {'Data': body_data, 'Charset': 'utf-8'}}    #TODO: use also in assert condition
        with open("../resources/mock/email_body_template_result_ok.html") as f:
            self.assertEqual(body_data, f.read())


if __name__ == '__main__':
    unittest.main()