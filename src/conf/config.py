from functools import lru_cache
from typing import Any
from pydantic import ConfigDict, field_validator, EmailStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Configuration settings for the application.

    This class loads environment variables from a .env file and provides them
    as easily accessible attributes. It includes settings for the database,
    email service, JWT authentication, and Cloudinary integration.

    :ivar SQLALCHEMY_DATABASE_URL: Database connection URL.
    :vartype SQLALCHEMY_DATABASE_URL: str
    :ivar MAIL_USERNAME: Username for the email service.
    :vartype MAIL_USERNAME: EmailStr
    :ivar MAIL_PASSWORD: Password for the email service.
    :vartype MAIL_PASSWORD: str
    :ivar MAIL_FROM: Sender email address.
    :vartype MAIL_FROM: EmailStr
    :ivar MAIL_PORT: Port for the email server.
    :vartype MAIL_PORT: int
    :ivar MAIL_SERVER: Hostname or IP of the email server.
    :vartype MAIL_SERVER: str
    :ivar MAIL_FROM_NAME: Display name for the sender email.
    :vartype MAIL_FROM_NAME: str
    :ivar MAIL_STARTTLS: Enable STARTTLS for email communication.
    :vartype MAIL_STARTTLS: bool
    :ivar MAIL_SSL_TLS: Enable SSL/TLS for email communication.
    :vartype MAIL_SSL_TLS: bool
    :ivar USE_CREDENTIALS: Use authentication credentials for email.
    :vartype USE_CREDENTIALS: bool
    :ivar VALIDATE_CERTS: Validate SSL/TLS certificates for email.
    :vartype VALIDATE_CERTS: bool
    :ivar SECRET_KEY: Secret key for JWT token signing.
    :vartype SECRET_KEY: str
    :ivar ALGORITHM: Algorithm used for JWT token signing (e.g., "HS256").
    :vartype ALGORITHM: str
    :ivar CLOUDINARY_NAME: Cloudinary cloud name.
    :vartype CLOUDINARY_NAME: str
    :ivar CLOUDINARY_API_KEY: Cloudinary API key.
    :vartype CLOUDINARY_API_KEY: str
    :ivar CLOUDINARY_API_SECRET: Cloudinary API secret.
    :vartype CLOUDINARY_API_SECRET: str
    """
    
    SQLALCHEMY_DATABASE_URL: str
    
    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool

    SECRET_KEY: str
    ALGORITHM: str

    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v: Any):
        """
        Validates that the ALGORITHM is either "HS256" or "HS512".

        :param v: The value of the ALGORITHM field.
        :type v: Any
        :raises ValueError: If the algorithm is not "HS256" or "HS512".
        :return: The validated algorithm value.
        :rtype: Any
        """
        if v not in ["HS256", "HS512"]:
            raise ValueError("algorithm must be HS256 or HS512")
        return v


    model_config = ConfigDict(extra='ignore', env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings() -> Settings:
    """
    Retrieves the application settings.

    This function is cached to ensure that settings are loaded only once.

    :return: An instance of the Settings class.
    :rtype: Settings
    """
    return Settings()
#settings = Settings()