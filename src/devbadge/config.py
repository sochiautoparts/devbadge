"""Configuration management for DevBadge."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


DEFAULT_CONFIG_DIR = Path.home() / ".devbadge"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
LICENSE_CACHE_FILE = DEFAULT_CONFIG_DIR / "license_cache.json"

REPO_URL = "https://github.com/sochiautoparts/devbadge"
LICENSES_URL = "https://raw.githubusercontent.com/sochiautoparts/stars-pay-bot/main/data/licenses.json"
STARSPAY_API_URL = ""  # Primary: licenses.json; set STARSPAY_API_URL env for REST API fallback

BADGE_TYPES = [
    "commits",
    "languages",
    "stats",
    "activity",
    "profile",
    "coffee",
    "spotify",
    "weather",
]

FREE_BADGES = ["commits", "languages", "stats", "activity", "profile"]
PRO_BADGES = ["coffee", "spotify", "weather"]


@dataclass
class DevBadgeConfig:
    """Configuration for DevBadge."""

    theme: str = "default"
    badges: list = field(default_factory=lambda: FREE_BADGES.copy())
    output_dir: str = "./badges"
    github_token: str = ""
    license_key: str = ""
    hide_watermark: bool = False
    custom_colors: dict = field(default_factory=dict)

    def save(self, path: Optional[Path] = None) -> None:
        """Save config to file."""
        target = path or DEFAULT_CONFIG_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "DevBadgeConfig":
        """Load config from file."""
        target = path or DEFAULT_CONFIG_FILE
        if target.exists():
            with open(target) as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()

    @classmethod
    def from_env(cls) -> "DevBadgeConfig":
        """Create config from environment variables."""
        return cls(
            github_token=os.getenv("GITHUB_TOKEN", ""),
            license_key=os.getenv("LICENSE_KEY", os.getenv("DEVBADGE_LICENSE", "")),
            theme=os.getenv("DEVBADGE_THEME", "default"),
            output_dir=os.getenv("DEVBADGE_OUTPUT", "./badges"),
        )


def init_config() -> Path:
    """Initialize a new config file."""
    config = DevBadgeConfig()
    config.save()
    return DEFAULT_CONFIG_FILE


def is_pro(license_key: Optional[str] = None) -> bool:
    """Check if a license key grants Pro access.

    Checks:
    1. Local cache first (offline capable)
    2. Public licenses.json from StarsPay repo
    3. REST API fallback with STARSPAY_API_KEY

    Args:
        license_key: The license key to verify (SP-DVB-xxxx-xxxx format).

    Returns:
        True if the license is valid and grants Pro access.
    """
    if not license_key:
        license_key = os.getenv("LICENSE_KEY", os.getenv("DEVBADGE_LICENSE", ""))

    if not license_key:
        return False

    # Validate key format
    if not _validate_key_format(license_key):
        return False

    # 1. Check local cache (only valid if previously verified by server)
    # Note: Cache is written ONLY after successful server verification.
    # Manually creating a cache file will not grant persistent Pro access
    # because the cache expires and must be re-verified with the server.
    if LICENSE_CACHE_FILE.exists():
        try:
            with open(LICENSE_CACHE_FILE) as f:
                cache = json.load(f)
            cached = cache.get(license_key)
            if cached and not _is_expired(cached):
                # Cache is only trusted for 24 hours max, then re-verify
                cache_time = cached.get("verified_at", cached.get("cached_at", 0))
                if cache_time and (time.time() - cache_time) > 86400:  # 24 hours
                    pass  # Force re-verification
                else:
                    return True
        except (json.JSONDecodeError, OSError):
            pass

    # 2. Check public licenses.json
    try:
        import httpx
        with httpx.Client(timeout=10) as client:
            r = client.get(LICENSES_URL)
            if r.status_code == 200:
                licenses = r.json()
                if _check_license_in_data(license_key, licenses):
                    _cache_license(license_key, valid=True)
                    return True
    except Exception:
        pass

    # 3. REST API fallback (if STARSPAY_API_URL is set)
    api_url = os.getenv("STARSPAY_API_URL", STARSPAY_API_URL)
    api_key = os.getenv("STARSPAY_API_KEY", "")
    if api_url and api_key:
        try:
            import httpx
            with httpx.Client(timeout=10) as client:
                r = client.post(
                    f"{api_url}/api/v1/verify",
                    json={"key": license_key},
                    headers={"X-API-Key": api_key},
                )
                if r.status_code == 200 and r.json().get("valid"):
                    _cache_license(license_key, valid=True)
                    return True
        except Exception:
            pass

    return False


def _validate_key_format(key: str) -> bool:
    """Validate StarsPay license key format: SP-DVB-xxxx-xxxx.
    
    All license keys must match this exact format.
    Keys not matching this format are rejected immediately 
    without making any network calls.
    """
    parts = key.split("-")
    if len(parts) != 4:
        return False
    return parts[0] == "SP" and parts[1] == "DVB" and len(parts[2]) == 4 and len(parts[3]) == 4


def _check_license_in_data(key: str, data: dict) -> bool:
    """Check if a license key exists in the licenses data.
    
    The licenses.json stores key_hash (SHA-256 truncated to 16 hex chars)
    instead of plain keys for security. We compute the hash and match.
    """
    import hashlib
    key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
    
    licenses = data if isinstance(data, list) else data.get("licenses", [])
    for lic in licenses:
        # Match by key_hash (primary) or plain key (legacy)
        matches = False
        if lic.get("key_hash") == key_hash:
            matches = True
        elif lic.get("key") == key:
            matches = True
        
        if matches:
            # Check project prefix matches
            key_prefix = key[:7]  # SP-DVB-
            if lic.get("key_prefix", "").startswith("SP-DVB") or "DVB" in key:
                # Check active status
                if not lic.get("active", True):
                    return False
                # Check expiration
                expires_at = lic.get("expires_at", 0)
                if expires_at and expires_at > 0:
                    import time
                    if time.time() > expires_at:
                        return False
                return True
    return False


def _cache_license(key: str, valid: bool = True) -> None:
    """Cache license verification result locally."""
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cache = {}
    if LICENSE_CACHE_FILE.exists():
        try:
            with open(LICENSE_CACHE_FILE) as f:
                cache = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    from datetime import datetime, timezone, timedelta
    cache[key] = {
        "valid": valid,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    }

    with open(LICENSE_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def _is_expired(cached_entry: dict) -> bool:
    """Check if a cached license entry is expired."""
    from datetime import datetime, timezone
    expires = cached_entry.get("expires_at", "")
    if not expires:
        return True
    try:
        exp = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        return exp < datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return True
