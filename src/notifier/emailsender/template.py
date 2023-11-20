from jinja2 import FileSystemLoader, Environment
from aws_lambda_powertools import Logger

logger = Logger()


class Singleton(type):
    """
    This class represents a metaclass useful to implement a singleton pattern
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class StonTemplate(metaclass=Singleton):
    """
    This class represents the email common templates for lambda.
    """

    def __init__(self, path=None):
        """

        :param path:
        """
        templates = FileSystemLoader(path if path is not None else "src/resources")
        self.__env = Environment(loader=templates)

    def get_template(self, filename):
        """
        This method load and return the real template useful to make a correct email.

        :param filename:
        :return:
        """
        return self.__env.get_template(filename)