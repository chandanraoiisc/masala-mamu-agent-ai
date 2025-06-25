import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    APP_NAME: str = "Kitchen Assistant"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Azure OpenAI settings
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Database settings (for inventory agent)
    # DB_CONNECTION_STRING: str = os.getenv("DB_CONNECTION_STRING", "")

    # # API keys for shopping platforms
    # BLINKIT_API_KEY: str = os.getenv("BLINKIT_API_KEY", "")
    # ZEPTO_API_KEY: str = os.getenv("ZEPTO_API_KEY", "")
    # INSTAMART_API_KEY: str = os.getenv("INSTAMART_API_KEY", "")

    class Config:
        env_file = ".env"


settings = Settings()
