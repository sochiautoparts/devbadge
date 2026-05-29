"""Tests for DevBadge badge generation."""

import pytest
from devbadge.badges import (
    CommitBadge,
    LanguageBadge,
    ActivityBadge,
    StatsBadge,
    CoffeeBadge,
    SpotifyBadge,
    WeatherBadge,
    generate_badge,
)
from devbadge.themes import get_theme, THEMES, list_themes, list_free_themes
from devbadge.config import is_pro, DevBadgeConfig, _validate_key_format
from devbadge.animations import pulse_animation, gradient_animation, typing_animation, sparkle_animation


class TestCommitBadge:
    """Test commit badge generation."""

    def test_basic_commit_badge(self):
        svg = CommitBadge.generate("testuser", 42)
        assert "<svg" in svg
        assert "</svg>" in svg
        assert "42" in svg
        assert "testuser" in svg
        assert "DevBadge" in svg  # watermark

    def test_commit_badge_no_watermark_for_pro(self):
        svg = CommitBadge.generate("testuser", 100, is_pro_user=True)
        assert "DevBadge" not in svg

    def test_commit_badge_large_count(self):
        svg = CommitBadge.generate("testuser", 15000)
        assert "15.0k" in svg

    def test_commit_badge_with_sparkline(self):
        data = list(range(60))
        svg = CommitBadge.generate("testuser", 500, contribution_data=data)
        assert "polyline" in svg

    def test_commit_badge_themes(self):
        for theme_name in THEMES:
            if not THEMES[theme_name].pro_only:
                svg = CommitBadge.generate("testuser", 42, theme=theme_name)
                assert "<svg" in svg


class TestLanguageBadge:
    """Test language badge generation."""

    def test_basic_language_badge(self):
        langs = [
            {"name": "Python", "bytes": 10000, "color": "#3572A5"},
            {"name": "JavaScript", "bytes": 5000, "color": "#f1e05a"},
        ]
        svg = LanguageBadge.generate(langs)
        assert "<svg" in svg
        assert "Python" in svg
        assert "JavaScript" in svg

    def test_empty_languages(self):
        svg = LanguageBadge.generate([])
        assert "<svg" in svg

    def test_single_language(self):
        langs = [{"name": "Rust", "bytes": 5000, "color": "#dea584"}]
        svg = LanguageBadge.generate(langs)
        assert "Rust" in svg
        assert "100%" in svg

    def test_many_languages(self):
        langs = [{"name": f"Lang{i}", "bytes": 1000 - i * 50, "color": "#ff0000"} for i in range(12)]
        svg = LanguageBadge.generate(langs)
        assert "<svg" in svg


class TestActivityBadge:
    """Test activity badge generation."""

    def test_basic_activity_badge(self):
        data = [0, 1, 2, 3, 5, 0, 0] * 16
        svg = ActivityBadge.generate(contribution_data=data)
        assert "<svg" in svg
        assert "Contribution Activity" in svg

    def test_empty_activity(self):
        svg = ActivityBadge.generate()
        assert "<svg" in svg

    def test_activity_with_theme(self):
        data = [5] * 112
        svg = ActivityBadge.generate(contribution_data=data, theme="dracula")
        assert "<svg" in svg


class TestStatsBadge:
    """Test stats badge generation."""

    def test_basic_stats_badge(self):
        svg = StatsBadge.generate(stars=100, forks=50, repos=20, followers=30)
        assert "<svg" in svg
        assert "100" in svg
        assert "50" in svg

    def test_large_numbers(self):
        svg = StatsBadge.generate(stars=1500000, forks=50000)
        assert "1.5M" in svg
        assert "50.0k" in svg

    def test_zero_values(self):
        svg = StatsBadge.generate()
        assert "<svg" in svg


class TestCoffeeBadge:
    """Test coffee badge generation."""

    def test_basic_coffee_badge(self):
        svg = CoffeeBadge.generate(coffee_count=5, username="dev")
        assert "<svg" in svg
        assert "5" in svg
        assert "☕" in svg

    def test_coffee_no_username(self):
        svg = CoffeeBadge.generate(coffee_count=0)
        assert "Coffees bought" in svg


class TestSpotifyBadge:
    """Test Spotify badge generation."""

    def test_basic_spotify_badge(self):
        svg = SpotifyBadge.generate(song="Bohemian Rhapsody", artist="Queen")
        assert "<svg" in svg
        assert "Bohemian Rhapsody" in svg
        assert "Queen" in svg

    def test_long_song_name(self):
        svg = SpotifyBadge.generate(song="A" * 50, artist="B")
        assert "…" in svg


class TestWeatherBadge:
    """Test weather badge generation."""

    def test_basic_weather_badge(self):
        svg = WeatherBadge.generate(temp="22°C", condition="Sunny", location="Moscow")
        assert "<svg" in svg
        assert "22°C" in svg
        assert "Sunny" in svg

    def test_weather_without_location(self):
        svg = WeatherBadge.generate(temp="15°C", condition="Cloudy")
        assert "15°C" in svg


class TestGenerateBadge:
    """Test the generate_badge dispatcher."""

    def test_all_free_badge_types(self):
        for badge_type in ["commits", "languages", "stats", "activity", "profile"]:
            svg = generate_badge(badge_type, username="testuser")
            assert "<svg" in svg

    def test_pro_badge_without_license(self):
        svg = generate_badge("coffee", is_pro_user=False)
        assert "Pro only" in svg

    def test_pro_badge_with_license(self):
        """Test Pro badge generation with a valid license (mocked)."""
        from unittest.mock import patch
        with patch("devbadge.badges.is_pro", return_value=True):
            svg = generate_badge("coffee", username="dev", coffee_count=3)
            assert "3" in svg
            assert "Pro only" not in svg

    def test_unknown_badge_type(self):
        with pytest.raises(ValueError, match="Unknown badge type"):
            generate_badge("nonexistent")


class TestThemes:
    """Test theme functionality."""

    def test_get_default_theme(self):
        theme = get_theme("default")
        assert theme.name == "default"
        assert theme.background == "#0d1b2a"

    def test_get_unknown_theme_fallback(self):
        theme = get_theme("nonexistent")
        assert theme.name == "default"

    def test_list_themes(self):
        themes = list_themes()
        assert len(themes) >= 6
        assert "default" in themes
        assert "dracula" in themes

    def test_list_free_themes(self):
        free = list_free_themes()
        assert "neon" not in free
        assert "aurora" not in free
        assert "default" in free

    def test_all_themes_have_required_fields(self):
        for name, theme in THEMES.items():
            assert theme.background, f"{name} missing background"
            assert theme.foreground, f"{name} missing foreground"
            assert theme.accent, f"{name} missing accent"


class TestConfig:
    """Test configuration."""

    def test_validate_key_format_valid(self):
        assert _validate_key_format("SP-DVB-abcd-1234") is True

    def test_validate_key_format_invalid(self):
        assert _validate_key_format("invalid") is False
        assert _validate_key_format("SP-XXX-abcd-1234") is False
        assert _validate_key_format("SP-DVB-ab-1234") is False

    def test_config_save_load(self, tmp_path):
        config = DevBadgeConfig(theme="dracula", output_dir="/tmp/test")
        path = tmp_path / "config.json"
        config.save(path)

        loaded = DevBadgeConfig.load(path)
        assert loaded.theme == "dracula"
        assert loaded.output_dir == "/tmp/test"

    def test_is_pro_no_key(self):
        assert is_pro("") is False
        assert is_pro(None) is False

    def test_is_pro_invalid_key(self):
        assert is_pro("not-a-key") is False


class TestAnimations:
    """Test animation generators."""

    def test_pulse_animation(self):
        anim = pulse_animation("test1", "#ff0000")
        assert "@keyframes pulse-test1" in anim
        assert "ff0000" in anim

    def test_gradient_animation(self):
        anim = gradient_animation("test2", ["#ff0000", "#00ff00", "#0000ff"])
        assert "linearGradient" in anim
        assert "@keyframes grad-shift-test2" in anim

    def test_typing_animation(self):
        anim = typing_animation("test3", "Hello World")
        assert "@keyframes typing-test3" in anim
        assert "880" in anim  # 11 chars * 80ms

    def test_sparkle_animation(self):
        anim = sparkle_animation("test4", count=3)
        assert "sparkle" in anim
        assert "@keyframes" in anim

    def test_apply_animation_not_pro(self):
        from devbadge.animations import apply_animation
        result = apply_animation("<svg>test</svg>", "pulse", "x1", is_pro=False)
        assert result == "<svg>test</svg>"

    def test_apply_animation_pro(self):
        from devbadge.animations import apply_animation
        result = apply_animation("<svg>test</svg>", "pulse", "x1", is_pro=True, color="#fff")
        assert "pulse" in result
