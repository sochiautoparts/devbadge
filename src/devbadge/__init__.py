"""DevBadge — Dynamic SVG badges for GitHub profiles."""

__version__ = "2.0.0"
__author__ = "sochiautoparts"

from devbadge.badges import (
    CommitBadge,
    LanguageBadge,
    ActivityBadge,
    StatsBadge,
    CoffeeBadge,
    SpotifyBadge,
    WeatherBadge,
    ProfileBadge,
    generate_badge,
)
from devbadge.themes import get_theme, THEMES

__all__ = [
    "__version__",
    "CommitBadge",
    "LanguageBadge",
    "ActivityBadge",
    "StatsBadge",
    "CoffeeBadge",
    "SpotifyBadge",
    "WeatherBadge",
    "ProfileBadge",
    "generate_badge",
    "get_theme",
    "THEMES",
]
