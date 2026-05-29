"""Tests for DevBadge badge generation."""

import json
import time
import pytest
from unittest.mock import patch, MagicMock

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
    _apply_custom_colors,
    _svg_icon_star,
    _svg_weather_icon,
)
from devbadge.themes import get_theme, THEMES, list_themes, list_free_themes, Theme
from devbadge.config import (
    is_pro,
    DevBadgeConfig,
    _validate_key_format,
    _cache_license,
    _is_expired,
    _sign_cache_entry,
    _verify_cache_signature,
    LICENSE_CACHE_FILE,
)
from devbadge.animations import (
    pulse_animation,
    gradient_animation,
    typing_animation,
    sparkle_animation,
    apply_animation,
)


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

    def test_commit_badge_custom_colors(self):
        svg = CommitBadge.generate("testuser", 42, custom_colors={"accent": "#ff0000"})
        assert "#ff0000" in svg

    def test_no_emoji_in_badge(self):
        """Verify no emoji characters in SVG output (Fix #4)."""
        svg = CommitBadge.generate("testuser", 42)
        # These emoji should NOT appear in SVG text elements
        for emoji in ["☕", "📦", "👥", "🎂", "★", "⑂", "🔀", "❗", "🔒", "🌤️", "🎵"]:
            assert emoji not in svg, f"Emoji {emoji} found in commit badge SVG"


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

    def test_stats_no_emoji(self):
        """Stats badge should use text labels, not emoji."""
        svg = StatsBadge.generate(stars=100, forks=50, repos=20)
        # No emoji characters
        for emoji in ["📦", "👥", "🔀", "❗"]:
            assert emoji not in svg
        # Should have plain text labels
        assert "Stars" in svg
        assert "Forks" in svg
        assert "Repos" in svg


class TestCoffeeBadge:
    """Test coffee badge generation."""

    def test_basic_coffee_badge(self):
        svg = CoffeeBadge.generate(coffee_count=5, username="dev")
        assert "<svg" in svg
        assert "5" in svg
        assert "cups" in svg  # No emoji, just text

    def test_coffee_no_username(self):
        svg = CoffeeBadge.generate(coffee_count=0)
        assert "Coffees bought" in svg

    def test_coffee_no_emoji(self):
        """Coffee badge should use SVG icon, not ☕ emoji."""
        svg = CoffeeBadge.generate(coffee_count=5, username="dev")
        assert "☕" not in svg
        # Should have SVG coffee cup shape instead
        assert "rect" in svg  # Coffee cup body


class TestSpotifyBadge:
    """Test Spotify badge generation."""

    def test_basic_spotify_badge(self):
        svg = SpotifyBadge.generate(song="Bohemian Rhapsody", artist="Queen")
        assert "<svg" in svg
        assert "Bohemian Rhapsody" in svg
        assert "Queen" in svg

    def test_long_song_name(self):
        svg = SpotifyBadge.generate(song="A" * 50, artist="B")
        assert "..." in svg

    def test_spotify_now_playing(self):
        svg = SpotifyBadge.generate(song="Test Song", artist="Artist", is_playing=True)
        assert "Now Playing" in svg
        assert "animate" in svg  # SMIL animation for playing indicator

    def test_spotify_last_played(self):
        svg = SpotifyBadge.generate(song="Test Song", artist="Artist", is_playing=False)
        assert "Last Played" in svg

    def test_spotify_no_emoji(self):
        svg = SpotifyBadge.generate(song="Song", artist="Artist")
        # Should have SVG icon, not emoji
        assert "🎵" not in svg


class TestWeatherBadge:
    """Test weather badge generation."""

    def test_basic_weather_badge(self):
        svg = WeatherBadge.generate(temp="22C", condition="Sunny", location="Moscow")
        assert "<svg" in svg
        assert "22C" in svg
        assert "Moscow" in svg

    def test_weather_without_location(self):
        svg = WeatherBadge.generate(temp="15C", condition="Cloudy")
        assert "15C" in svg

    def test_weather_with_icon(self):
        svg = WeatherBadge.generate(temp="5C", condition="Rain", icon_svg="rain")
        assert "<svg" in svg
        # Should have rain SVG icon
        assert "rain" not in svg or "line" in svg  # Weather icon renders as SVG

    def test_weather_no_emoji(self):
        svg = WeatherBadge.generate(temp="22C", condition="Sunny")
        assert "🌤️" not in svg

    def test_all_weather_icons(self):
        """Test that all weather icon types render without errors."""
        for icon_name in ["sun", "cloud-sun", "cloud", "rain", "snow", "thunder", "fog"]:
            svg = _svg_weather_icon(icon_name, 0, 0, "#ffd700")
            assert len(svg) > 0


class TestProfileBadge:
    """Test profile badge generation."""

    def test_basic_profile_badge(self):
        svg = ProfileBadge.generate(name="TestUser", repos=10, followers=5, age_days=730)
        assert "<svg" in svg
        assert "TestUser" in svg
        assert "10" in svg
        assert "5" in svg
        assert "2y on GitHub" in svg

    def test_profile_with_bio(self):
        svg = ProfileBadge.generate(name="User", bio="Hello world")
        assert "Hello world" in svg

    def test_profile_no_emoji(self):
        svg = ProfileBadge.generate(name="User", repos=5, followers=10, age_days=365)
        for emoji in ["📦", "👥", "🎂"]:
            assert emoji not in svg


class TestCustomColors:
    """Test custom color override support (Fix #7)."""

    def test_custom_accent_color(self):
        colors = {"accent": "#ff0000"}
        svg = CommitBadge.generate("user", 42, custom_colors=colors)
        assert "#ff0000" in svg

    def test_custom_background_color(self):
        colors = {"background": "#000000"}
        svg = StatsBadge.generate(custom_colors=colors)
        assert "#000000" in svg

    def test_apply_custom_colors_function(self):
        theme = get_theme("default")
        custom = {"accent": "#00ff00", "background": "#111111"}
        modified = _apply_custom_colors(theme, custom)
        assert modified.accent == "#00ff00"
        assert modified.background == "#111111"
        # Original theme should be unchanged
        assert theme.accent != "#00ff00"

    def test_empty_custom_colors(self):
        theme = get_theme("default")
        modified = _apply_custom_colors(theme, {})
        assert modified.accent == theme.accent

    def test_custom_color_primary_maps_to_accent(self):
        theme = get_theme("default")
        custom = {"primary": "#abcdef"}
        modified = _apply_custom_colors(theme, custom)
        assert modified.accent == "#abcdef"


class TestGenerateBadge:
    """Test the generate_badge dispatcher."""

    def test_all_free_badge_types(self):
        for badge_type in ["commits", "languages", "stats", "activity", "profile"]:
            svg = generate_badge(badge_type, username="testuser")
            assert "<svg" in svg

    def test_pro_badge_without_license(self):
        svg = generate_badge("coffee", is_pro_user=False)
        assert "Pro only" in svg or "Pro" in svg

    def test_pro_badge_with_license(self):
        """Test Pro badge generation with a valid license (mocked)."""
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

    def test_config_custom_colors_field(self):
        config = DevBadgeConfig(custom_colors={"accent": "#ff0000"})
        assert config.custom_colors == {"accent": "#ff0000"}

    def test_config_spotify_weather_fields(self):
        config = DevBadgeConfig(spotify_token="test_token", weather_city="Moscow")
        assert config.spotify_token == "test_token"
        assert config.weather_city == "Moscow"

    def test_is_pro_no_key(self):
        assert is_pro("") is False
        assert is_pro(None) is False

    def test_is_pro_invalid_key(self):
        assert is_pro("not-a-key") is False


class TestCacheSecurity:
    """Test HMAC cache signing (Fix #8)."""

    def test_sign_and_verify_cache_entry(self):
        data = {"valid": True, "verified_ts": time.time(), "expires_ts": time.time() + 86400}
        sig = _sign_cache_entry(data, "SP-DVB-test-1234")
        data["sig"] = sig
        assert _verify_cache_signature(data, "SP-DVB-test-1234") is True

    def test_wrong_key_fails_verification(self):
        data = {"valid": True, "verified_ts": time.time()}
        sig = _sign_cache_entry(data, "SP-DVB-test-1234")
        data["sig"] = sig
        # Different key should fail
        assert _verify_cache_signature(data, "SP-DVB-test-5678") is False

    def test_no_signature_fails_verification(self):
        data = {"valid": True, "verified_ts": time.time()}
        assert _verify_cache_signature(data, "SP-DVB-test-1234") is False

    def test_tampered_data_fails_verification(self):
        data = {"valid": True, "verified_ts": time.time()}
        sig = _sign_cache_entry(data, "SP-DVB-test-1234")
        data["sig"] = sig
        # Tamper with data
        data["valid"] = False
        assert _verify_cache_signature(data, "SP-DVB-test-1234") is False

    def test_cache_license_adds_signature(self, tmp_path):
        """Test that _cache_license adds HMAC signature."""
        import devbadge.config as config_mod
        original_file = config_mod.LICENSE_CACHE_FILE
        config_mod.LICENSE_CACHE_FILE = tmp_path / "license_cache.json"
        config_mod.DEFAULT_CONFIG_DIR = tmp_path

        try:
            _cache_license("SP-DVB-test-1234", valid=True)

            with open(config_mod.LICENSE_CACHE_FILE) as f:
                cache = json.load(f)

            entry = cache.get("SP-DVB-test-1234")
            assert entry is not None
            assert "sig" in entry
            assert "verified_ts" in entry
            assert "expires_ts" in entry
            assert _verify_cache_signature(entry, "SP-DVB-test-1234") is True
        finally:
            config_mod.LICENSE_CACHE_FILE = original_file


class TestCacheTimestamp:
    """Test that cache timestamps use Unix timestamps (Fix #2)."""

    def test_is_expired_uses_unix_timestamp(self):
        # Not expired: future timestamp
        entry = {"expires_ts": time.time() + 86400}
        assert _is_expired(entry) is False

        # Expired: past timestamp
        entry = {"expires_ts": time.time() - 86400}
        assert _is_expired(entry) is True

    def test_is_expired_fallback_to_iso(self):
        from datetime import datetime, timezone, timedelta
        # Future ISO timestamp
        future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        entry = {"expires_at": future}
        assert _is_expired(entry) is False

        # Past ISO timestamp
        past = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        entry = {"expires_at": past}
        assert _is_expired(entry) is True


class TestAnimations:
    """Test SMIL animation generators (Fix #5)."""

    def test_pulse_animation_uses_smil(self):
        anim = pulse_animation("test1", "#ff0000")
        assert "<animate" in anim
        assert "@keyframes" not in anim  # No CSS
        assert "<style" not in anim  # No style tags

    def test_gradient_animation_uses_smil(self):
        anim = gradient_animation("test2", ["#ff0000", "#00ff00", "#0000ff"])
        assert "linearGradient" in anim
        assert "<animate" in anim  # SMIL animate on stops
        assert "@keyframes" not in anim  # No CSS
        assert "<style" not in anim

    def test_typing_animation_uses_smil(self):
        anim = typing_animation("test3", "Hello World")
        assert "clipPath" in anim
        assert "<animate" in anim  # SMIL animate on width
        assert "@keyframes" not in anim  # No CSS
        assert "<style" not in anim

    def test_sparkle_animation_uses_smil(self):
        anim = sparkle_animation("test4", count=3)
        assert "sparkle" in anim
        assert "<animate" in anim  # SMIL animate on opacity
        assert "<animateTransform" in anim  # SMIL transform
        assert "@keyframes" not in anim  # No CSS
        assert "<style" not in anim

    def test_apply_animation_not_pro(self):
        result = apply_animation("<svg>test</svg>", "pulse", "x1", is_pro=False)
        assert result == "<svg>test</svg>"

    def test_apply_animation_pro_pulse(self):
        result = apply_animation("<svg>test</svg>", "pulse", "x1", is_pro=True, color="#fff")
        assert "<animate" in result
        assert "@keyframes" not in result

    def test_apply_animation_pro_gradient(self):
        result = apply_animation("<svg>content</svg>", "gradient", "x1", is_pro=True,
                                colors=["#ff0000", "#00ff00"])
        assert "linearGradient" in result
        assert "<animate" in result

    def test_no_css_style_tags_in_any_animation(self):
        """Verify all animation types use SMIL only, no CSS (Fix #5)."""
        for anim_func, kwargs in [
            (pulse_animation, {"element_id": "t1", "color": "#fff"}),
            (gradient_animation, {"element_id": "t2", "colors": ["#f00", "#0f0"]}),
            (typing_animation, {"element_id": "t3", "text": "Hello"}),
            (sparkle_animation, {"element_id": "t4", "count": 2}),
        ]:
            result = anim_func(**kwargs)
            assert "<style" not in result, f"{anim_func.__name__} contains <style> tag"
            assert "@keyframes" not in result, f"{anim_func.__name__} contains CSS @keyframes"


class TestSVGIconHelpers:
    """Test SVG icon helper functions."""

    def test_star_icon(self):
        icon = _svg_icon_star(10, 10, 8, "#ffd700")
        assert "polygon" in icon
        assert "#ffd700" in icon

    def test_weather_icon_all_types(self):
        for icon_type in ["sun", "cloud-sun", "cloud", "rain", "snow", "thunder", "fog", "unknown"]:
            icon = _svg_weather_icon(icon_type, 0, 0, "#ffd700")
            assert len(icon) > 0
            assert "<" in icon  # Should be SVG markup
