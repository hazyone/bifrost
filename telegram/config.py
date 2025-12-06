"""
Configuration module for Telegram client.
Loads settings from environment variables or .env file.

Official client credentials sourced from:
- https://github.com/thedemons/opentele
- https://github.com/telegramdesktop/tdesktop
"""

import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


@dataclass
class DeviceInfo:
    """Device fingerprint for Telegram connection."""
    api_id: int
    api_hash: str
    device_model: str
    system_version: str
    app_version: str
    lang_code: str
    system_lang_code: str
    lang_pack: str  # NOTE: Telethon ignores this, but we store for reference


class OfficialClients:
    """
    Official Telegram client credentials.

    api_id and api_hash are PERMANENT identifiers - they don't change.
    app_version should be updated periodically to match current releases.

    Sources:
    - https://github.com/thedemons/opentele (api_id/hash, last updated 2022)
    - https://github.com/telegramdesktop/tdesktop/releases (versions)

    Last updated: December 2024
    """

    # Telegram Desktop (Windows/Linux/macOS)
    # api_id 2040 = "Public Win Beta" - permanent identifier
    # Source: https://github.com/telegramdesktop/tdesktop
    TDESKTOP = DeviceInfo(
        api_id=2040,
        api_hash="b18441a1ff607e10a989891a5462e627",
        device_model="Desktop",
        system_version="Windows 10",
        app_version="5.9.0 x64",  # Updated Dec 2024
        lang_code="en",
        system_lang_code="en-US",
        lang_pack="tdesktop",
    )

    # Telegram for Android
    # api_id 6 = original Android app - permanent identifier
    # Source: https://github.com/DrKLO/Telegram
    ANDROID = DeviceInfo(
        api_id=6,
        api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e",
        device_model="Samsung SM-S928B",  # Galaxy S24 Ultra
        system_version="SDK 34",  # Android 14
        app_version="11.5.0 (5516)",  # Updated Dec 2024
        lang_code="en",
        system_lang_code="en-US",
        lang_pack="android",
    )

    # Telegram X for Android
    # api_id 21724 - permanent identifier
    ANDROID_X = DeviceInfo(
        api_id=21724,
        api_hash="3e0cb5efcd52300aec5994fdfc5bdc16",
        device_model="Samsung SM-S928B",
        system_version="SDK 34",
        app_version="0.26.6 (1954)",  # Telegram X updates less frequently
        lang_code="en",
        system_lang_code="en-US",
        lang_pack="android",
    )

    # Telegram for iOS
    # api_id 10840 - permanent identifier
    IOS = DeviceInfo(
        api_id=10840,
        api_hash="33c45224029d59cb3ad0c16134215aeb",
        device_model="iPhone 16 Pro Max",
        system_version="18.1",  # iOS 18
        app_version="11.5",  # Updated Dec 2024
        lang_code="en",
        system_lang_code="en-US",
        lang_pack="ios",
    )

    # Telegram for macOS (Swift)
    # api_id 2834 - permanent identifier
    MACOS = DeviceInfo(
        api_id=2834,
        api_hash="68875f756c9b437a8b916ca3de215815",
        device_model="MacBook Pro",
        system_version="macOS 15.1",  # Sequoia
        app_version="11.5",  # Updated Dec 2024
        lang_code="en",
        system_lang_code="en-US",
        lang_pack="macos",
    )

    # Telegram Web Z/K
    # api_id 2496 - permanent identifier
    WEB = DeviceInfo(
        api_id=2496,
        api_hash="8da85b0d5bfe62527e5b244c209159c3",
        device_model="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        system_version="Windows",
        app_version="2.1.0 A",  # Updated Dec 2024
        lang_code="en",
        system_lang_code="en-US",
        lang_pack="",
    )

    # TDesktop test credentials (very limited, for testing only)
    TDESKTOP_TEST = DeviceInfo(
        api_id=17349,
        api_hash="344583e45741c457fe1862106095a5eb",
        device_model="Desktop",
        system_version="Windows 10",
        app_version="5.9.0 x64",  # Updated Dec 2024
        lang_code="en",
        system_lang_code="en-US",
        lang_pack="tdesktop",
    )

    # TDesktop nightly/public credentials
    TDESKTOP_NIGHTLY = DeviceInfo(
        api_id=611335,
        api_hash="d524b414d21f4d37f08684c1df41ac9c",
        device_model="Desktop",
        system_version="Windows 10",
        app_version="5.9.0 x64",  # Updated Dec 2024
        lang_code="en",
        system_lang_code="en-US",
        lang_pack="tdesktop",
    )


# Device model variations for randomization (updated Dec 2024)
ANDROID_DEVICES = [
    "Samsung SM-S928B",   # Galaxy S24 Ultra
    "Samsung SM-S926B",   # Galaxy S24+
    "Samsung SM-S921B",   # Galaxy S24
    "Samsung SM-S918B",   # Galaxy S23 Ultra
    "Google Pixel 9 Pro XL",
    "Google Pixel 9 Pro",
    "Google Pixel 8 Pro",
    "OnePlus 12",
    "Xiaomi 14 Pro",
]

IOS_DEVICES = [
    "iPhone 16 Pro Max",
    "iPhone 16 Pro",
    "iPhone 15 Pro Max",
    "iPhone 15 Pro",
    "iPhone 14 Pro Max",
]

MACOS_DEVICES = [
    "MacBook Pro",
    "MacBook Air",
    "Mac mini",
    "iMac",
    "Mac Studio",
]


def get_randomized_device(base: DeviceInfo, unique_id: str | None = None) -> DeviceInfo:
    """
    Get device info with randomized model.

    If unique_id is provided, the randomization will be deterministic
    (same unique_id = same device).
    """
    if unique_id:
        random.seed(hash(unique_id))

    if base.lang_pack == "android":
        device = random.choice(ANDROID_DEVICES)
        sdk = random.choice(["SDK 31", "SDK 32", "SDK 33", "SDK 34"])
        return DeviceInfo(
            api_id=base.api_id,
            api_hash=base.api_hash,
            device_model=device,
            system_version=sdk,
            app_version=base.app_version,
            lang_code=base.lang_code,
            system_lang_code=base.system_lang_code,
            lang_pack=base.lang_pack,
        )
    elif base.lang_pack == "ios":
        device = random.choice(IOS_DEVICES)
        ios_version = random.choice(["17.2", "17.1", "17.0", "16.7"])
        return DeviceInfo(
            api_id=base.api_id,
            api_hash=base.api_hash,
            device_model=device,
            system_version=ios_version,
            app_version=base.app_version,
            lang_code=base.lang_code,
            system_lang_code=base.system_lang_code,
            lang_pack=base.lang_pack,
        )
    elif base.lang_pack == "macos":
        device = random.choice(MACOS_DEVICES)
        macos_version = random.choice(["macOS 14.2", "macOS 14.1", "macOS 13.6"])
        return DeviceInfo(
            api_id=base.api_id,
            api_hash=base.api_hash,
            device_model=device,
            system_version=macos_version,
            app_version=base.app_version,
            lang_code=base.lang_code,
            system_lang_code=base.system_lang_code,
            lang_pack=base.lang_pack,
        )

    return base


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    fetch_delay: float = 1.0  # Seconds between requests
    batch_size: int = 100  # Messages per batch


@dataclass
class Config:
    """Main configuration for Telegram client."""
    device: DeviceInfo
    phone_number: str
    session_name: str
    target_group: str | None
    rate_limit: RateLimitConfig

    @property
    def api_id(self) -> int:
        return self.device.api_id

    @property
    def api_hash(self) -> str:
        return self.device.api_hash

    @classmethod
    def from_env(cls, client_type: str = "tdesktop") -> "Config":
        """
        Load configuration from environment variables.

        Args:
            client_type: Which official client to mimic.
                Options: tdesktop, android, ios, macos, web, custom
        """
        # Load .env file if exists
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        phone_number = os.getenv("PHONE_NUMBER")
        if not phone_number:
            raise ValueError("PHONE_NUMBER environment variable is required")

        # Get client type from env or use default
        client_type = os.getenv("CLIENT_TYPE", client_type).lower()

        # Select device info based on client type
        if client_type == "android":
            device = OfficialClients.ANDROID
        elif client_type == "android_x":
            device = OfficialClients.ANDROID_X
        elif client_type == "ios":
            device = OfficialClients.IOS
        elif client_type == "macos":
            device = OfficialClients.MACOS
        elif client_type == "web":
            device = OfficialClients.WEB
        elif client_type == "custom":
            # Use custom API credentials from env
            api_id = os.getenv("API_ID")
            api_hash = os.getenv("API_HASH")
            if not api_id or not api_hash:
                raise ValueError("API_ID and API_HASH required for custom client type")
            device = DeviceInfo(
                api_id=int(api_id),
                api_hash=api_hash,
                device_model=os.getenv("DEVICE_MODEL", "Desktop"),
                system_version=os.getenv("SYSTEM_VERSION", "Windows 10"),
                app_version=os.getenv("APP_VERSION", "5.8.3 x64"),
                lang_code=os.getenv("LANG_CODE", "en"),
                system_lang_code=os.getenv("SYSTEM_LANG_CODE", "en-US"),
                lang_pack=os.getenv("LANG_PACK", "tdesktop"),
            )
        else:  # tdesktop (default)
            device = OfficialClients.TDESKTOP

        # Apply randomization if requested
        if os.getenv("RANDOMIZE_DEVICE", "").lower() in ("1", "true", "yes"):
            unique_id = os.getenv("SESSION_NAME", "default")
            device = get_randomized_device(device, unique_id)

        return cls(
            device=device,
            phone_number=phone_number,
            session_name=os.getenv("SESSION_NAME", "telegram_session"),
            target_group=os.getenv("TARGET_GROUP"),
            rate_limit=RateLimitConfig(
                fetch_delay=float(os.getenv("FETCH_DELAY", "1.0")),
                batch_size=int(os.getenv("BATCH_SIZE", "100")),
            ),
        )
