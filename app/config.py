import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BaseConfig:
    APP_NAME = "Open Targets AI API"
    DEBUG = False
    CORS_ORIGINS = []

    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    CORS_ORIGINS = ["http://localhost:3000"]


class ProductionConfig(BaseConfig):
    DEBUG = False
    CORS_ORIGINS = [""]


def get_config():
    """Get configuration based on environment."""
    env = os.getenv("APP_ENV", "development")
    if env == "production":
        config = ProductionConfig()
    else:
        config = DevelopmentConfig()

    # Validate configuration
    config.validate_config()
    return config
