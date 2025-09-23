import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def load_openai_token():
    """
    Load OpenAI token from environment variable or file.

    Supports multiple methods:
    1. OPENAI_TOKEN environment variable
    2. OPENAI_API_KEY environment variable (for compatibility)
    3. OPENAI_TOKEN_FILE environment variable pointing to a file containing the token

    Returns:
        str: The OpenAI API token
    """
    # Try OPENAI_TOKEN first (preferred)
    token = os.getenv("OPENAI_TOKEN")
    if token:
        return token

    # Try OPENAI_API_KEY for compatibility
    token = os.getenv("OPENAI_API_KEY")
    if token:
        return token

    # Try loading from file
    token_file = os.getenv("OPENAI_TOKEN_FILE")
    if token_file:
        try:
            with open(token_file, "r") as f:
                return f.read().strip()
        except Exception as e:
            raise ValueError(f"Failed to read OpenAI token from file {token_file}: {e}")

    return None


class BaseConfig:
    APP_NAME = "Open Targets AI API"
    DEBUG = False
    CORS_ORIGINS = []

    # OpenAI Configuration
    OPENAI_API_KEY = load_openai_token()

    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OpenAI token is required. Please set one of: "
                "OPENAI_TOKEN, OPENAI_API_KEY, or OPENAI_TOKEN_FILE environment variables"
            )


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
