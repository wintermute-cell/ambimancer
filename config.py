import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Default settings
    FLASK_ENV = 'development'
    DEBUG = False
    TESTING = False

    # Settings applicable to all environments
    SECRET_KEY = os.getenv('SECRET_KEY', default='devkey')


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    FLASK_ENV = 'production'
