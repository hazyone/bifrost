"""
Configuration module for Telegram client.
Loads settings from environment variables or .env file.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    fetch_delay: float = 1.0  # Seconds between requests
    batch_size: int = 100  # Messages per batch


@dataclass
class Config:
    """Main configuration for Telegram client."""
    api_id: int
    api_hash: str
    phone_number: str
    session_name: str
    target_group: str | None
    rate_limit: RateLimitConfig

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        # Load .env file if exists
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH")
        phone_number = os.getenv("PHONE_NUMBER")

        if not api_id or not api_hash or not phone_number:
            raise ValueError(
                "Missing required environment variables. "
                "Please set API_ID, API_HASH, and PHONE_NUMBER. "
                "Get your API credentials at https://my.telegram.org/apps"
            )

        return cls(
            api_id=int(api_id),
            api_hash=api_hash,
            phone_number=phone_number,
            session_name=os.getenv("SESSION_NAME", "telegram_session"),
            target_group=os.getenv("TARGET_GROUP"),
            rate_limit=RateLimitConfig(
                fetch_delay=float(os.getenv("FETCH_DELAY", "1.0")),
                batch_size=int(os.getenv("BATCH_SIZE", "100")),
            ),
        )


# Known API credentials from public sources (TDesktop)
# These appear as official Telegram Desktop client
class KnownCredentials:
    """Public API credentials from TDesktop builds."""

    # TDesktop nightly build credentials
    TDESKTOP_API_ID = 611335
    TDESKTOP_API_HASH = "d524b414d21f4d37f08684c1df41ac9c"

    # TDesktop test credentials (very limited)
    TDESKTOP_TEST_API_ID = 17349
    TDESKTOP_TEST_API_HASH = "344583e45741c457fe1862106095a5eb"
