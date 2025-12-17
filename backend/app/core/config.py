import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    SecretStr,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    # Use SecretStr to prevent accidental logging of secret key (NFR-S7)
    SECRET_KEY: SecretStr = SecretStr(secrets.token_urlsafe(32))
    # JWT RS256 keys for asymmetric signing (AC: #10)
    JWT_PRIVATE_KEY: SecretStr = SecretStr("")
    JWT_PUBLIC_KEY: str = ""
    # Access token: 30 minutes (security best practice, AC: #1)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Refresh token: 7 days (AC: #1, #7)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    # Use SecretStr to prevent accidental logging of password (NFR-S7)
    POSTGRES_PASSWORD: SecretStr = SecretStr("")
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    # MinIO Object Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ROOT_USER: str = ""
    # Use SecretStr to prevent accidental logging of password (NFR-S7)
    MINIO_ROOT_PASSWORD: SecretStr = SecretStr("")
    MINIO_USE_SSL: bool = False
    MINIO_BUCKET_NAME: str = "assets"

    # Logging Configuration
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"

    # Rate Limiting Configuration (Story 2.4)
    # Format: "X/second", "X/minute", "X/hour", "X/day"
    RATE_LIMIT_PUBLISHER: str = "1000/hour"
    RATE_LIMIT_SCHOOL: str = "1000/hour"
    RATE_LIMIT_TEACHER: str = "500/hour"
    RATE_LIMIT_STUDENT: str = "100/hour"
    RATE_LIMIT_DEFAULT: str = "100/hour"  # For unauthenticated requests
    RATE_LIMIT_LOGIN: str = "5/minute"  # Brute force protection
    RATE_LIMIT_SIGNUP: str = "10/minute"  # Signup abuse protection

    # File Upload Configuration (Story 3.1)
    # MIME types whitelist (AC: #2)
    ALLOWED_MIME_TYPES: list[str] = [
        "application/pdf",
        "video/mp4",
        "video/webm",
        "video/quicktime",
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/ogg",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/zip",
        "application/json",
        "text/plain",
    ]

    # File size limits in bytes (AC: #1, NFR-P3, Story 3.4 AC: #5)
    MAX_FILE_SIZE_VIDEO: int = 10 * 1024 * 1024 * 1024  # 10GB
    MAX_FILE_SIZE_IMAGE: int = 500 * 1024 * 1024  # 500MB
    MAX_FILE_SIZE_AUDIO: int = 100 * 1024 * 1024  # 100MB (Story 3.4)
    MAX_FILE_SIZE_DEFAULT: int = 5 * 1024 * 1024 * 1024  # 5GB

    # Presigned URL Configuration (Story 3.2)
    # Upload URLs: 15 minutes TTL for security (AC: #2)
    PRESIGNED_URL_UPLOAD_EXPIRES_SECONDS: int = 900
    # Download URLs: 1 hour TTL for classroom usage (AC: #3)
    PRESIGNED_URL_DOWNLOAD_EXPIRES_SECONDS: int = 3600
    # Stream URLs: 1 hour TTL for video/audio streaming (same as download)
    PRESIGNED_URL_STREAM_EXPIRES_SECONDS: int = 3600

    # ZIP Upload Configuration (Story 3.3)
    # Maximum ZIP file size (10GB per NFR-P3)
    MAX_ZIP_FILE_SIZE: int = 10_737_418_240  # 10GB
    # Maximum files to extract (prevent zip bomb)
    MAX_ZIP_EXTRACTED_FILES: int = 1000
    # Maximum total extracted size (50GB limit)
    MAX_EXTRACTED_TOTAL_SIZE: int = 53_687_091_200  # 50GB
    # Maximum compression ratio (zip bomb protection)
    MAX_ZIP_COMPRESSION_RATIO: int = 100
    # System file patterns to filter during extraction (FR3)
    FILTERED_ZIP_PATTERNS: list[str] = [
        r"\.DS_Store$",
        r"__MACOSX/",
        r"Thumbs\.db$",
        r"\.git/",
        r"desktop\.ini$",
        r"\.tmp$",
        r"~\$",
        r"\.swp$",
        r"\.swo$",
        r"node_modules/",
        r"__pycache__/",
        r"\.pyc$",
    ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def minio_secure(self) -> bool:
        return self.MINIO_USE_SSL

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    def _check_default_secret(
        self, var_name: str, value: str | SecretStr | None
    ) -> None:
        # Handle SecretStr by extracting the actual value
        actual_value = (
            value.get_secret_value() if isinstance(value, SecretStr) else value
        )
        if actual_value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = Settings()  # type: ignore
