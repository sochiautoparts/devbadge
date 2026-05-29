"""Core SVG badge generator for DevBadge.

Each badge type generates a standalone SVG that renders correctly
in GitHub READMEs without any external dependencies.
"""

from __future__ import annotations

import html
import math
import uuid
from typing import Dict, List, Optional

from devbadge.themes import Theme, get_theme, LANGUAGE_COLORS
from devbadge.config import is_pro, REPO_URL, FREE_BADGES, PRO_BADGES


def _escape(text: str) -> str:
    """Escape text for safe inclusion in SVG."""
    return html.escape(str(text), quote=True)


def _watermark(is_pro_user: bool = False, y_offset: int = 0) -> str:
    """Generate a small DevBadge watermark. Pro users get no watermark."""
    if is_pro_user:
        return ""
    return f"""<a href="{REPO_URL}" target="_blank">
    <text x="4" y="{y_offset}" font-family="Arial, sans-serif" font-size="8" fill="#666666" opacity="0.6">DevBadge</text>
  </a>"""


def _svg_wrapper(width: int, height: int, content: str, theme: Theme) -> str:
    """Wrap content in a standard SVG element with theme styling."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" rx="6" fill="{theme.background}" />
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="5.5" fill="none" stroke="{theme.border}" stroke-width="1" opacity="0.3" />
{content}
</svg>"""


class CommitBadge:
    """Generate a commit count badge with sparkline graph."""

    @staticmethod
    def generate(
        username: str,
        commit_count: int,
        contribution_data: Optional[List[int]] = None,
        theme: str = "default",
        is_pro_user: bool = False,
    ) -> str:
        """Generate commit badge SVG.

        Args:
            username: GitHub username.
            commit_count: Total number of commits.
            contribution_data: List of daily contribution counts for sparkline.
            theme: Theme name.
            is_pro_user: Whether the user has Pro license.

        Returns:
            SVG string.
        """
        t = get_theme(theme)
        uid = uuid.uuid4().hex[:8]

        # Sparkline from contribution data (last 30 days)
        sparkline = ""
        if contribution_data and len(contribution_data) > 30:
            last_30 = contribution_data[-30:]
            max_val = max(last_30) if max(last_30) > 0 else 1
            points = []
            chart_x_start = 140
            chart_width = 180
            chart_y_start = 28
            chart_height = 20
            for i, val in enumerate(last_30):
                x = chart_x_start + (i / 29) * chart_width
                y = chart_y_start + chart_height - (val / max_val) * chart_height
                points.append(f"{x:.1f},{y:.1f}")
            if len(points) > 1:
                sparkline = f"""<polyline points="{' '.join(points)}" fill="none" stroke="{t.accent}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.8" />"""
                # Fill area under sparkline
                area_points = " ".join(points)
                first_x = chart_x_start
                last_x = chart_x_start + chart_width
                sparkline = f"""<path d="M{points[0].split(',')[0]},{chart_y_start + chart_height} L{area_points} L{last_x},{chart_y_start + chart_height} Z" fill="{t.accent}" opacity="0.1" />
    {sparkline}"""

        # Format commit count
        if commit_count >= 1000:
            count_text = f"{commit_count / 1000:.1f}k"
        else:
            count_text = str(commit_count)

        width = 340
        height = 50

        # Commit icon (simple git commit dot)
        icon = f"""<circle cx="24" cy="25" r="6" fill="none" stroke="{t.accent}" stroke-width="2" />
    <circle cx="24" cy="25" r="2" fill="{t.accent}" />
    <line x1="24" y1="19" x2="24" y2="10" stroke="{t.accent}" stroke-width="2" />
    <line x1="24" y1="31" x2="24" y2="40" stroke="{t.accent}" stroke-width="2" />"""

        content = f"""  <text x="42" y="22" font-family="Arial, sans-serif" font-size="11" font-weight="600" fill="{t.title_color}">{_escape(username)}'s commits</text>
  <text x="42" y="40" font-family="'Courier New', monospace" font-size="18" font-weight="700" fill="{t.accent}">{_escape(count_text)}</text>
  <g transform="translate(0, 0)">
    {icon}
  </g>
  {sparkline}
  {_watermark(is_pro_user, height - 4)}"""

        return _svg_wrapper(width, height, content, t)


class LanguageBadge:
    """Generate a top-languages bar badge."""

    @staticmethod
    def generate(
        languages: List[dict],
        theme: str = "default",
        is_pro_user: bool = False,
    ) -> str:
        """Generate language badge SVG.

        Args:
            languages: List of dicts with 'name', 'bytes', 'color' keys.
            theme: Theme name.
            is_pro_user: Whether the user has Pro license.

        Returns:
            SVG string.
        """
        t = get_theme(theme)
        uid = uuid.uuid4().hex[:8]

        if not languages:
            languages = [{"name": "N/A", "bytes": 1, "color": t.muted}]

        total = sum(lang.get("bytes", 0) for lang in languages)
        if total == 0:
            total = 1

        width = 340
        bar_height = 10
        bar_y = 20
        bar_x = 12
        bar_width = width - 24

        # Language bar segments
        segments = ""
        current_x = bar_x
        for lang in languages[:8]:
            seg_width = (lang.get("bytes", 0) / total) * bar_width
            color = lang.get("color", t.muted)
            if seg_width > 0:
                segments += f"""<rect x="{current_x:.1f}" y="{bar_y}" width="{seg_width:.1f}" height="{bar_height}" fill="{color}" />"""
                current_x += seg_width

        # Language labels below the bar
        labels = ""
        label_x = 12
        label_y = bar_y + bar_height + 16
        for i, lang in enumerate(languages[:5]):
            name = lang.get("name", "?")
            pct = (lang.get("bytes", 0) / total) * 100
            color = lang.get("color", t.muted)
            label_text = f"{name} {pct:.0f}%"
            labels += f"""<circle cx="{label_x}" cy="{label_y - 4}" r="4" fill="{color}" />
    <text x="{label_x + 8}" y="{label_y}" font-family="Arial, sans-serif" font-size="10" fill="{t.text_color}">{_escape(label_text)}</text>
"""
            # Calculate width for next label
            text_width = len(label_text) * 6.5 + 18
            label_x += text_width
            if label_x > width - 60:
                break

        # Title
        title = f"""<text x="{width // 2}" y="14" font-family="Arial, sans-serif" font-size="11" font-weight="600" fill="{t.title_color}" text-anchor="middle">Top Languages</text>"""

        height = max(label_y + 10, 50)
        watermark = _watermark(is_pro_user, height - 4)

        content = f"""  {title}
  {segments}
  {labels}
  {watermark}"""

        return _svg_wrapper(width, height, content, t)


class ActivityBadge:
    """Generate a contribution heatmap-style mini grid."""

    @staticmethod
    def generate(
        contribution_data: Optional[List[int]] = None,
        theme: str = "default",
        is_pro_user: bool = False,
    ) -> str:
        """Generate activity badge SVG.

        Args:
            contribution_data: List of daily contribution counts.
            theme: Theme name.
            is_pro_user: Whether the user has Pro license.

        Returns:
            SVG string.
        """
        t = get_theme(theme)

        if not contribution_data:
            contribution_data = [0] * 364

        # Take last 16 weeks (112 days) for a compact grid
        data = contribution_data[-112:] if len(contribution_data) >= 112 else contribution_data[-len(contribution_data):]
        while len(data) < 112:
            data.insert(0, 0)

        width = 340
        cell_size = 8
        cell_gap = 2
        grid_x_start = 12
        grid_y_start = 24

        # Intensity levels
        max_val = max(data) if max(data) > 0 else 1

        def intensity_color(val: int) -> str:
            if val == 0:
                return t.secondary
            ratio = min(val / max_val, 1.0)
            if ratio < 0.25:
                return t.accent + "33"
            elif ratio < 0.5:
                return t.accent + "66"
            elif ratio < 0.75:
                return t.accent + "99"
            else:
                return t.accent

        grid = ""
        for week in range(16):
            for day in range(7):
                idx = week * 7 + day
                if idx >= len(data):
                    break
                x = grid_x_start + week * (cell_size + cell_gap)
                y = grid_y_start + day * (cell_size + cell_gap)
                color = intensity_color(data[idx])
                grid += f"""<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="1" fill="{color}" />"""

        # Title
        title = f"""<text x="{width // 2}" y="16" font-family="Arial, sans-serif" font-size="11" font-weight="600" fill="{t.title_color}" text-anchor="middle">Contribution Activity</text>"""

        height = grid_y_start + 7 * (cell_size + cell_gap) + 8
        watermark = _watermark(is_pro_user, height - 4)

        content = f"""  {title}
  {grid}
  {watermark}"""

        return _svg_wrapper(width, height, content, t)


class StatsBadge:
    """Generate a stats overview badge."""

    @staticmethod
    def generate(
        stars: int = 0,
        forks: int = 0,
        repos: int = 0,
        followers: int = 0,
        prs: int = 0,
        issues: int = 0,
        theme: str = "default",
        is_pro_user: bool = False,
    ) -> str:
        """Generate stats badge SVG.

        Args:
            stars: Total star count.
            forks: Total fork count.
            repos: Number of public repos.
            followers: Follower count.
            prs: PR count.
            issues: Issue count.
            theme: Theme name.
            is_pro_user: Whether the user has Pro license.

        Returns:
            SVG string.
        """
        t = get_theme(theme)

        width = 340
        height = 100

        def fmt(n: int) -> str:
            if n >= 1000000:
                return f"{n / 1000000:.1f}M"
            if n >= 1000:
                return f"{n / 1000:.1f}k"
            return str(n)

        # Stats items in a grid layout
        stats = [
            ("★ Stars", fmt(stars), t.accent),
            ("⑂ Forks", fmt(forks), t.muted),
            ("📦 Repos", fmt(repos), t.accent),
            ("👥 Followers", fmt(followers), t.muted),
            ("🔀 PRs", fmt(prs), t.accent),
            ("❗ Issues", fmt(issues), t.muted),
        ]

        items = ""
        col_width = 105
        row_height = 28
        start_y = 24

        for i, (label, value, color) in enumerate(stats):
            col = i % 3
            row = i // 3
            x = 14 + col * col_width
            y = start_y + row * row_height

            items += f"""<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="9" fill="{t.muted}">{_escape(label)}</text>
    <text x="{x}" y="{y + 14}" font-family="'Courier New', monospace" font-size="14" font-weight="700" fill="{color}">{_escape(value)}</text>
"""

        # Title
        title = f"""<text x="{width // 2}" y="14" font-family="Arial, sans-serif" font-size="11" font-weight="600" fill="{t.title_color}" text-anchor="middle">GitHub Stats</text>"""

        watermark = _watermark(is_pro_user, height - 4)

        content = f"""  {title}
  {items}
  {watermark}"""

        return _svg_wrapper(width, height, content, t)


class CoffeeBadge:
    """Generate a fun 'bought X coffees' badge (Pro only)."""

    @staticmethod
    def generate(
        coffee_count: int = 0,
        username: str = "",
        theme: str = "default",
        is_pro_user: bool = False,
    ) -> str:
        """Generate coffee badge SVG.

        Args:
            coffee_count: Number of coffees.
            username: GitHub username.
            theme: Theme name.
            is_pro_user: Whether the user has Pro license.

        Returns:
            SVG string.
        """
        t = get_theme(theme)

        width = 220
        height = 50

        # Coffee cup icon
        cup = f"""<g transform="translate(14, 12)">
      <rect x="2" y="6" width="16" height="16" rx="2" fill="{t.accent}" opacity="0.3" />
      <rect x="4" y="8" width="12" height="12" rx="1" fill="{t.accent}" opacity="0.6" />
      <path d="M18 10 C22 10 22 18 18 18" fill="none" stroke="{t.accent}" stroke-width="1.5" />
      <line x1="6" y1="5" x2="6" y2="2" stroke="{t.muted}" stroke-width="1.5" stroke-linecap="round" />
      <line x1="10" y1="4" x2="10" y2="1" stroke="{t.muted}" stroke-width="1.5" stroke-linecap="round" />
      <line x1="14" y1="5" x2="14" y2="2" stroke="{t.muted}" stroke-width="1.5" stroke-linecap="round" />
    </g>"""

        label = f"{username} bought" if username else "Coffees bought"
        content = f"""  {cup}
  <text x="48" y="22" font-family="Arial, sans-serif" font-size="11" fill="{t.muted}">{_escape(label)}</text>
  <text x="48" y="40" font-family="'Courier New', monospace" font-size="16" font-weight="700" fill="{t.accent}">{_escape(str(coffee_count))} ☕</text>
  {_watermark(is_pro_user, height - 4)}"""

        return _svg_wrapper(width, height, content, t)


class SpotifyBadge:
    """Generate a now-playing Spotify badge (Pro only, placeholder)."""

    @staticmethod
    def generate(
        song: str = "Not playing",
        artist: str = "—",
        theme: str = "default",
        is_pro_user: bool = False,
    ) -> str:
        """Generate Spotify now-playing badge SVG.

        Args:
            song: Currently playing song title.
            artist: Artist name.
            theme: Theme name.
            is_pro_user: Whether the user has Pro license.

        Returns:
            SVG string.
        """
        t = get_theme(theme)

        width = 280
        height = 50

        # Spotify-like icon
        icon = f"""<g transform="translate(12, 10)">
      <circle cx="14" cy="14" r="14" fill="#1DB954" opacity="0.2" />
      <circle cx="14" cy="14" r="10" fill="#1DB954" opacity="0.4" />
      <path d="M10 18 C10 14 18 12 20 10" fill="none" stroke="#1DB954" stroke-width="2" stroke-linecap="round" />
      <path d="M10 22 C10 18 20 15 22 14" fill="none" stroke="#1DB954" stroke-width="1.5" stroke-linecap="round" />
    </g>"""

        # Truncate long text
        song_display = song[:28] + "…" if len(song) > 28 else song
        artist_display = artist[:24] + "…" if len(artist) > 24 else artist

        content = f"""  {icon}
  <text x="46" y="22" font-family="Arial, sans-serif" font-size="11" font-weight="600" fill="{t.foreground}">{_escape(song_display)}</text>
  <text x="46" y="38" font-family="Arial, sans-serif" font-size="10" fill="{t.muted}">{_escape(artist_display)}</text>
  {_watermark(is_pro_user, height - 4)}"""

        return _svg_wrapper(width, height, content, t)


class WeatherBadge:
    """Generate a current weather badge (Pro only, placeholder)."""

    @staticmethod
    def generate(
        temp: str = "—",
        condition: str = "Unknown",
        location: str = "",
        theme: str = "default",
        is_pro_user: bool = False,
    ) -> str:
        """Generate weather badge SVG.

        Args:
            temp: Temperature string (e.g., "22°C").
            condition: Weather condition (e.g., "Sunny").
            location: Location string.
            theme: Theme name.
            is_pro_user: Whether the user has Pro license.

        Returns:
            SVG string.
        """
        t = get_theme(theme)

        width = 200
        height = 50

        # Simple weather icon (sun)
        icon = f"""<g transform="translate(14, 12)">
      <circle cx="12" cy="12" r="6" fill="{t.accent}" />
      <line x1="12" y1="2" x2="12" y2="5" stroke="{t.accent}" stroke-width="2" stroke-linecap="round" />
      <line x1="12" y1="19" x2="12" y2="22" stroke="{t.accent}" stroke-width="2" stroke-linecap="round" />
      <line x1="2" y1="12" x2="5" y2="12" stroke="{t.accent}" stroke-width="2" stroke-linecap="round" />
      <line x1="19" y1="12" x2="22" y2="12" stroke="{t.accent}" stroke-width="2" stroke-linecap="round" />
      <line x1="5" y1="5" x2="7" y2="7" stroke="{t.accent}" stroke-width="2" stroke-linecap="round" />
      <line x1="17" y1="17" x2="19" y2="19" stroke="{t.accent}" stroke-width="2" stroke-linecap="round" />
      <line x1="5" y1="19" x2="7" y2="17" stroke="{t.accent}" stroke-width="2" stroke-linecap="round" />
      <line x1="17" y1="7" x2="19" y2="5" stroke="{t.accent}" stroke-width="2" stroke-linecap="round" />
    </g>"""

        content = f"""  {icon}
  <text x="46" y="22" font-family="'Courier New', monospace" font-size="16" font-weight="700" fill="{t.accent}">{_escape(temp)}</text>
  <text x="46" y="38" font-family="Arial, sans-serif" font-size="10" fill="{t.muted}">{_escape(condition)}{' · ' + _escape(location) if location else ''}</text>
  {_watermark(is_pro_user, height - 4)}"""

        return _svg_wrapper(width, height, content, t)


def generate_badge(
    badge_type: str,
    stats: Optional[object] = None,
    theme: str = "default",
    is_pro_user: bool = False,
    **kwargs,
) -> str:
    """Generate a badge by type name.

    Args:
        badge_type: One of 'commits', 'languages', 'stats', 'activity',
                    'profile', 'coffee', 'spotify', 'weather'.
        stats: UserStats object (from github_stats).
        theme: Theme name.
        is_pro_user: Whether the user has Pro license.
        **kwargs: Additional parameters for specific badge types.

    Returns:
        SVG string.
    """
    # Check if Pro badge is requested without license
    if badge_type in PRO_BADGES and not is_pro_user:
        return _pro_required_badge(badge_type, theme)

    generators = {
        "commits": _gen_commits,
        "languages": _gen_languages,
        "stats": _gen_stats,
        "activity": _gen_activity,
        "profile": _gen_profile,
        "coffee": _gen_coffee,
        "spotify": _gen_spotify,
        "weather": _gen_weather,
    }

    generator = generators.get(badge_type)
    if not generator:
        raise ValueError(f"Unknown badge type: {badge_type}. Available: {list(generators.keys())}")

    return generator(stats=stats, theme=theme, is_pro_user=is_pro_user, **kwargs)


def _gen_commits(stats, theme, is_pro_user, **kwargs) -> str:
    """Generate commit badge from stats."""
    if stats:
        return CommitBadge.generate(
            username=stats.username,
            commit_count=stats.total_commits,
            contribution_data=stats.contribution_data,
            theme=theme,
            is_pro_user=is_pro_user,
        )
    return CommitBadge.generate(
        username=kwargs.get("username", "user"),
        commit_count=kwargs.get("commit_count", 0),
        contribution_data=kwargs.get("contribution_data"),
        theme=theme,
        is_pro_user=is_pro_user,
    )


def _gen_languages(stats, theme, is_pro_user, **kwargs) -> str:
    """Generate language badge from stats."""
    if stats and stats.languages:
        langs = [{"name": l.name, "bytes": l.bytes, "color": l.color} for l in stats.languages]
    else:
        langs = kwargs.get("languages", [])
    return LanguageBadge.generate(languages=langs, theme=theme, is_pro_user=is_pro_user)


def _gen_stats(stats, theme, is_pro_user, **kwargs) -> str:
    """Generate stats badge."""
    # StatsBadge.generate only accepts specific kwargs
    valid_keys = {"stars", "forks", "repos", "followers", "prs", "issues"}
    filtered = {k: v for k, v in kwargs.items() if k in valid_keys}
    if stats:
        return StatsBadge.generate(
            stars=stats.total_stars,
            forks=stats.total_forks,
            repos=stats.public_repos,
            followers=stats.followers,
            prs=stats.total_prs,
            issues=stats.total_issues,
            theme=theme,
            is_pro_user=is_pro_user,
        )
    return StatsBadge.generate(theme=theme, is_pro_user=is_pro_user, **filtered)


def _gen_activity(stats, theme, is_pro_user, **kwargs) -> str:
    """Generate activity badge."""
    if stats:
        return ActivityBadge.generate(
            contribution_data=stats.contribution_data,
            theme=theme,
            is_pro_user=is_pro_user,
        )
    return ActivityBadge.generate(
        contribution_data=kwargs.get("contribution_data"),
        theme=theme,
        is_pro_user=is_pro_user,
    )


def _gen_profile(stats, theme, is_pro_user, **kwargs) -> str:
    """Generate a profile overview badge."""
    t = get_theme(theme)
    width = 340
    height = 80

    if stats:
        name = stats.name or stats.username
        bio = stats.bio
        repos = stats.public_repos
        followers = stats.followers
        age_days = stats.account_age_days
    else:
        name = kwargs.get("username", "User")
        bio = kwargs.get("bio", "")
        repos = kwargs.get("repos", 0)
        followers = kwargs.get("followers", 0)
        age_days = kwargs.get("age_days", 0)

    age_years = age_days // 365

    content = f"""  <text x="170" y="20" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="{t.title_color}" text-anchor="middle">{_escape(name)}</text>"""
    if bio:
        bio_display = bio[:50] + "…" if len(bio) > 50 else bio
        content += f"""
  <text x="170" y="36" font-family="Arial, sans-serif" font-size="10" fill="{t.muted}" text-anchor="middle">{_escape(bio_display)}</text>"""

    content += f"""
  <text x="80" y="58" font-family="Arial, sans-serif" font-size="10" fill="{t.muted}" text-anchor="middle">📦 {repos} repos</text>
  <text x="170" y="58" font-family="Arial, sans-serif" font-size="10" fill="{t.muted}" text-anchor="middle">👥 {followers} followers</text>
  <text x="260" y="58" font-family="Arial, sans-serif" font-size="10" fill="{t.muted}" text-anchor="middle">🎂 {age_years}y on GitHub</text>
  {_watermark(is_pro_user, height - 4)}"""

    return _svg_wrapper(width, height, content, t)


def _gen_coffee(stats, theme, is_pro_user, **kwargs) -> str:
    """Generate coffee badge."""
    return CoffeeBadge.generate(
        coffee_count=kwargs.get("coffee_count", 0),
        username=kwargs.get("username", ""),
        theme=theme,
        is_pro_user=is_pro_user,
    )


def _gen_spotify(stats, theme, is_pro_user, **kwargs) -> str:
    """Generate Spotify badge."""
    return SpotifyBadge.generate(
        song=kwargs.get("song", "Not playing"),
        artist=kwargs.get("artist", "—"),
        theme=theme,
        is_pro_user=is_pro_user,
    )


def _gen_weather(stats, theme, is_pro_user, **kwargs) -> str:
    """Generate weather badge."""
    return WeatherBadge.generate(
        temp=kwargs.get("temp", "—"),
        condition=kwargs.get("condition", "Unknown"),
        location=kwargs.get("location", ""),
        theme=theme,
        is_pro_user=is_pro_user,
    )


def _pro_required_badge(badge_type: str, theme: str = "default") -> str:
    """Generate a 'Pro required' placeholder badge."""
    t = get_theme(theme)
    width = 220
    height = 36

    content = f"""  <text x="110" y="22" font-family="Arial, sans-serif" font-size="11" fill="{t.muted}" text-anchor="middle">🔒 {_escape(badge_type.title())} — Pro only</text>
  {_watermark(False, height - 4)}"""

    return _svg_wrapper(width, height, content, t)
