import os
from dotenv import load_dotenv, find_dotenv


ENVFILE = find_dotenv()
if ENVFILE:
    load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Default settings
    FLASK_ENV = 'development'
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'ambimancer.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Settings applicable to all environments
    SECRET_KEY = os.getenv('SECRET_KEY', default='devkey')

    AUTH0_LOGOUT_URL = './auth/logout'
    AUTH0_CALLBACK_URL = './auth/callback'


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    FLASK_ENV = 'production'
