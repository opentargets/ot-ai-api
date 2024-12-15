import os


class BaseConfig:
    APP_NAME = "Open Targets AI API"
    DEBUG = False
    CORS_ORIGINS = []


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    CORS_ORIGINS = ["http://localhost:3000"]


class ProductionConfig(BaseConfig):
    DEBUG = False
    CORS_ORIGINS = [""]


def get_config():
    env = os.getenv("APP_ENV", "development")
    if env == "production":
        return ProductionConfig
    return DevelopmentConfig
