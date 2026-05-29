"""Configuration management for DevBadge."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
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

# Cache TTL: 24 hours max before re-verification required
CACHE_TTL_SECONDS = 86400

# HMAC key for cache file integrity — derived from license key at cache time
# This prevents trivial manual creation of cache files.
_HMAC_SECRET_SALT = "devbadge-cache-integrity-v1"


def _hmac_key_for_license(license_key: str) -> bytes:
    """Derive an HMAC key from the license key for cache signing.

    The HMAC key is derived by hashing the license key with a static salt.
    This means only someone who knows the license key can create a valid
    cache signature for that key.
    """
    return hashlib.sha256(f"{_HMAC_SECRET_SALT}:{license_key}".encode()).digest()


def _sign_cache_entry(data: dict, license_key: str) -> str:
    """Create HMAC signature for a cache entry.

    Signs the canonical JSON representation of the cache data (without
    the 'sig' field) using a key derived from the license key.
    """
    # Remove sig field if present for canonical signing
    canonical = {k: v for k, v in sorted(data.items()) if k != "sig"}
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    key = _hmac_key_for_license(license_key)
    return hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()


def _verify_cache_signature(data: dict, license_key: str) -> bool:
    """Verify the HMAC signature of a cache entry.

    Returns True if the signature is valid, False otherwise.
    """
    sig = data.get("sig", "")
    if not sig:
        return False
    expected_sig = _sign_cache_entry(data, license_key)
    return hmac.compare_digest(sig, expected_sig)


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
    spotify_token: str = ""
    weather_city: str = ""

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
            spotify_token=os.getenv("SPOTIFY_TOKEN", ""),
            weather_city=os.getenv("DEVBADGE_WEATHER_CITY", ""),
        )


def init_config() -> Path:
    """Initialize a new config file."""
    config = DevBadgeConfig()
    config.save()
    return DEFAULT_CONFIG_FILE


def is_pro(license_key: Optional[str] = None) -> bool:
    """Check if a license key grants Pro access.

    Checks:
    1. Local cache first (offline capable, HMAC-signed)
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

    # 1. Check local cache (HMAC-signed, only valid after server verification)
    if LICENSE_CACHE_FILE.exists():
        try:
            with open(LICENSE_CACHE_FILE) as f:
                cache = json.load(f)
            cached = cache.get(license_key)
            if cached:
                # Verify HMAC signature — prevents manual cache file creation
                if not _verify_cache_signature(cached, license_key):
                    # Invalid or missing signature — ignore this cache entry
                    pass
                elif _is_expired(cached):
                    pass  # Expired, force re-verification
                else:
                    # Check 24-hour re-verification window using Unix timestamp
                    verified_ts = cached.get("verified_ts", 0)
                    if verified_ts and (time.time() - verified_ts) > CACHE_TTL_SECONDS:
                        pass  # Force re-verification after 24 hours
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
                    if time.time() > expires_at:
                        return False
                return True
    return False


def _cache_license(key: str, valid: bool = True) -> None:
    """Cache license verification result locally with HMAC signature.

    The cache entry is signed with an HMAC derived from the license key,
    so manually creating a cache file without knowing the key will fail
    signature verification.
    """
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cache = {}
    if LICENSE_CACHE_FILE.exists():
        try:
            with open(LICENSE_CACHE_FILE) as f:
                cache = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    from datetime import datetime, timezone, timedelta
    now = time.time()
    cache[key] = {
        "valid": valid,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "verified_ts": now,  # Unix timestamp for fast comparison
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "expires_ts": now + 7 * 86400,  # Unix timestamp for fast comparison
    }

    # Sign the cache entry with HMAC
    cache[key]["sig"] = _sign_cache_entry(cache[key], key)

    with open(LICENSE_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def _is_expired(cached_entry: dict) -> bool:
    """Check if a cached license entry is expired.

    Uses Unix timestamp (expires_ts) for reliable comparison,
    with ISO string (expires_at) as fallback.
    """
    # Prefer Unix timestamp (fast, reliable)
    expires_ts = cached_entry.get("expires_ts", 0)
    if expires_ts:
        return time.time() > expires_ts

    # Fallback to ISO string parsing
    from datetime import datetime, timezone
    expires = cached_entry.get("expires_at", "")
    if not expires:
        return True
    try:
        exp = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        return exp < datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return True
