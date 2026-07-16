import os

from dotenv import load_dotenv

# APP_ENV only selects which .env file(s) get loaded — all config values
# themselves come from the environment, with safe (restrictive) defaults.
APP_ENV = os.getenv('APP_ENV', 'development')

# Load shared defaults first, then let a per-environment file override them,
# e.g. .env.development for permissive local defaults. Neither file is
# required to exist.
load_dotenv()
load_dotenv(f'.env.{APP_ENV}', override=True)


def load_openai_token():
    """Load OpenAI token from environment variable or file.

    Supports multiple methods:
    1. OPENAI_TOKEN environment variable
    2. OPENAI_API_KEY environment variable (for compatibility)
    3. OPENAI_TOKEN_FILE environment variable pointing to a file containing the token

    Returns:
        str: The OpenAI API token
    """
    # Try OPENAI_TOKEN first (preferred)
    token = os.getenv('OPENAI_TOKEN')
    if token:
        return token

    # Try OPENAI_API_KEY for compatibility
    token = os.getenv('OPENAI_API_KEY')
    if token:
        return token

    # Try loading from file
    token_file = os.getenv('OPENAI_TOKEN_FILE')
    if token_file:
        try:
            with open(token_file) as f:
                return f.read().strip()
        except Exception as e:
            raise ValueError(f'Failed to read OpenAI token from file {token_file}: {e}')

    return None


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


def _list_env(name: str, default: list[str]) -> list[str]:
    """Read `name` from the environment as a comma-separated list.

    Falls back to `default` when unset.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    return [o.strip() for o in raw.split(',') if o.strip()]


class Config:
    APP_NAME = 'Open Targets AI API'

    # Defaults are deliberately restrictive: no debug mode, no allowed CORS
    # origins. Permissive local values belong in a .env.development file,
    # e.g. DEBUG=true and CORS_ORIGINS=*.
    DEBUG = _bool_env('DEBUG', False)
    CORS_ORIGINS = _list_env('CORS_ORIGINS', [])

    # OpenAI Configuration
    OPENAI_API_KEY = load_openai_token()

    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                'OpenAI token is required. Please set one of: '
                'OPENAI_TOKEN, OPENAI_API_KEY, or OPENAI_TOKEN_FILE environment variables'
            )


def get_config():
    """Get configuration, populated from environment variables.

    See APP_ENV above for which .env file is loaded.
    """
    config = Config()
    config.validate_config()
    return config
