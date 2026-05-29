"""Core SVG badge generator for DevBadge.

Each badge type generates a standalone SVG that renders correctly
in GitHub READMEs without any external dependencies.

No emoji characters are used in SVG <text> elements — they don't
render reliably across platforms. Instead, we use simple SVG shapes
and plain text labels.
"""

from __future__ import annotations

import html
from typing import Dict, List, Optional

from devbadge.themes import Theme, get_theme, LANGUAGE_COLORS
from devbadge.config import is_pro, REPO_URL, FREE_BADGES, PRO_BADGES, DevBadgeConfig


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


def _apply_custom_colors(theme: Theme, custom_colors: dict) -> Theme:
    """Apply custom color overrides from config to a theme.

    Supported keys: primary, secondary, accent, background, foreground,
                    muted, border, title_color, text_color
    """
    if not custom_colors:
        return theme

    color_map = {
        "primary": "accent",
        "secondary": "secondary",
        "accent": "accent",
        "background": "background",
        "foreground": "foreground",
        "muted": "muted",
        "border": "border",
        "title_color": "title_color",
        "text_color": "text_color",
    }

    # Create a copy so we don't mutate the original theme
    import dataclasses
    t = dataclasses.replace(theme)

    for config_key, theme_attr in color_map.items():
        if config_key in custom_colors and custom_colors[config_key]:
            setattr(t, theme_attr, custom_colors[config_key])

    return t


def _svg_wrapper(width: int, height: int, content: str, theme: Theme) -> str:
    """Wrap content in a standard SVG element with theme styling."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" rx="6" fill="{theme.background}" />
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="5.5" fill="none" stroke="{theme.border}" stroke-width="1" opacity="0.3" />
{content}
</svg>"""


# ---- SVG Icon Helpers (no emoji) ----

def _svg_icon_star(x: int, y: int, size: int = 8, color: str = "#ffd700") -> str:
    """Draw a star icon using SVG polygon."""
    # 5-pointed star using polygon points
    import math
    points = []
    for i in range(5):
        outer_angle = math.radians(-90 + i * 72)
        inner_angle = math.radians(-90 + i * 72 + 36)
        outer_r = size
        inner_r = size * 0.4
        points.append(f"{x + outer_r * math.cos(outer_angle):.1f},{y + outer_r * math.sin(outer_angle):.1f}")
        points.append(f"{x + inner_r * math.cos(inner_angle):.1f},{y + inner_r * math.sin(inner_angle):.1f}")
    return f'<polygon points="{" ".join(points)}" fill="{color}" />'


def _svg_icon_fork(x: int, y: int, size: int = 8, color: str = "#888") -> str:
    """Draw a fork/branch icon using SVG lines and circles."""
    s = size
    return f"""<g transform="translate({x},{y})">
    <circle cx="{s*0.3}" cy="{s*0.2}" r="2" fill="{color}" />
    <circle cx="{s*0.7}" cy="{s*0.2}" r="2" fill="{color}" />
    <circle cx="{s*0.3}" cy="{s*0.8}" r="2" fill="{color}" />
    <line x1="{s*0.3}" y1="{s*0.4}" x2="{s*0.3}" y2="{s*0.6}" stroke="{color}" stroke-width="1.5" />
    <line x1="{s*0.7}" y1="{s*0.4}" x2="{s*0.5}" y2="{s*0.6}" stroke="{color}" stroke-width="1.5" />
    <line x1="{s*0.3}" y1="{s*0.6}" x2="{s*0.5}" y2="{s*0.6}" stroke="{color}" stroke-width="1.5" />
  </g>"""


def _svg_icon_repo(x: int, y: int, size: int = 8, color: str = "#888") -> str:
    """Draw a repo/book icon using SVG rect."""
    s = size
    return f"""<g transform="translate({x},{y})">
    <rect x="0" y="0" width="{s}" height="{s*1.2}" rx="1" fill="none" stroke="{color}" stroke-width="1.5" />
    <line x1="0" y1="{s*0.35}" x2="{s}" y2="{s*0.35}" stroke="{color}" stroke-width="1" />
  </g>"""


def _svg_icon_people(x: int, y: int, size: int = 8, color: str = "#888") -> str:
    """Draw a people/followers icon using SVG circles."""
    s = size
    return f"""<g transform="translate({x},{y})">
    <circle cx="{s*0.35}" cy="{s*0.25}" r="2.5" fill="{color}" />
    <path d="M{s*0.1},{s*0.9} Q{s*0.1},{s*0.5} {s*0.35},{s*0.5} Q{s*0.6},{s*0.5} {s*0.6},{s*0.9}" fill="{color}" opacity="0.7" />
    <circle cx="{s*0.75}" cy="{s*0.3}" r="2" fill="{color}" opacity="0.6" />
    <path d="M{s*0.55},{s*0.9} Q{s*0.55},{s*0.6} {s*0.75},{s*0.6} Q{s*0.95},{s*0.6} {s*0.95},{s*0.9}" fill="{color}" opacity="0.4" />
  </g>"""


def _svg_icon_pr(x: int, y: int, size: int = 8, color: str = "#888") -> str:
    """Draw a PR/merge icon using SVG paths."""
    s = size
    return f"""<g transform="translate({x},{y})">
    <circle cx="{s*0.3}" cy="{s*0.2}" r="2" fill="{color}" />
    <circle cx="{s*0.3}" cy="{s*0.8}" r="2" fill="{color}" />
    <circle cx="{s*0.7}" cy="{s*0.2}" r="2" fill="{color}" />
    <line x1="{s*0.3}" y1="{s*0.4}" x2="{s*0.3}" y2="{s*0.6}" stroke="{color}" stroke-width="1.5" />
    <path d="M{s*0.7},{s*0.4} Q{s*0.7},{s*0.6} {s*0.3},{s*0.6}" fill="none" stroke="{color}" stroke-width="1.5" />
  </g>"""


def _svg_icon_issue(x: int, y: int, size: int = 8, color: str = "#888") -> str:
    """Draw an issue icon (circle with dot) using SVG."""
    s = size
    cx = x + s * 0.5
    cy = y + s * 0.5
    r = s * 0.45
    return f"""<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="1.5" />
  <circle cx="{cx}" cy="{cy}" r="1.5" fill="{color}" />"""


def _svg_icon_coffee(x: int, y: int, color: str = "#888") -> str:
    """Draw a coffee cup icon using SVG shapes."""
    return f"""<g transform="translate({x},{y})">
    <rect x="2" y="4" width="14" height="12" rx="2" fill="{color}" opacity="0.6" />
    <path d="M16 7 C20 7 20 13 16 13" fill="none" stroke="{color}" stroke-width="1.5" />
    <path d="M5 3 Q7 0 9 3" fill="none" stroke="{color}" stroke-width="1" stroke-linecap="round" />
    <path d="M9 2 Q11 -1 13 2" fill="none" stroke="{color}" stroke-width="1" stroke-linecap="round" />
  </g>"""


def _svg_icon_spotify(x: int, y: int, color: str = "#1DB954") -> str:
    """Draw a Spotify icon using SVG."""
    return f"""<g transform="translate({x},{y})">
    <circle cx="14" cy="14" r="13" fill="{color}" opacity="0.15" />
    <circle cx="14" cy="14" r="9" fill="{color}" opacity="0.3" />
    <path d="M8 17 C8 13 18 11 22 9" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" />
    <path d="M8 21 C8 17 20 14 24 13" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" />
    <path d="M9 24 C10 21 18 19 22 18" fill="none" stroke="{color}" stroke-width="1" stroke-linecap="round" />
  </g>"""


def _svg_weather_icon(icon_name: str, x: int, y: int, color: str = "#ffd700") -> str:
    """Draw a weather icon based on the icon name."""
    if icon_name == "sun":
        return f"""<g transform="translate({x},{y})">
      <circle cx="12" cy="12" r="5" fill="{color}" />
      <line x1="12" y1="2" x2="12" y2="5" stroke="{color}" stroke-width="2" stroke-linecap="round" />
      <line x1="12" y1="19" x2="12" y2="22" stroke="{color}" stroke-width="2" stroke-linecap="round" />
      <line x1="2" y1="12" x2="5" y2="12" stroke="{color}" stroke-width="2" stroke-linecap="round" />
      <line x1="19" y1="12" x2="22" y2="12" stroke="{color}" stroke-width="2" stroke-linecap="round" />
      <line x1="5" y1="5" x2="7" y2="7" stroke="{color}" stroke-width="1.5" stroke-linecap="round" />
      <line x1="17" y1="17" x2="19" y2="19" stroke="{color}" stroke-width="1.5" stroke-linecap="round" />
      <line x1="5" y1="19" x2="7" y2="17" stroke="{color}" stroke-width="1.5" stroke-linecap="round" />
      <line x1="17" y1="7" x2="19" y2="5" stroke="{color}" stroke-width="1.5" stroke-linecap="round" />
    </g>"""
    elif icon_name == "cloud-sun":
        return f"""<g transform="translate({x},{y})">
      <circle cx="8" cy="8" r="4" fill="{color}" opacity="0.8" />
      <line x1="8" y1="1" x2="8" y2="3" stroke="{color}" stroke-width="1.5" stroke-linecap="round" />
      <line x1="2" y1="8" x2="4" y2="8" stroke="{color}" stroke-width="1.5" stroke-linecap="round" />
      <path d="M8 16 Q8 12 14 12 Q20 12 20 16 Q24 16 24 20 L4 20 Q4 16 8 16 Z" fill="white" opacity="0.7" />
    </g>"""
    elif icon_name == "cloud":
        return f"""<g transform="translate({x},{y})">
      <path d="M6 20 Q2 20 2 16 Q2 12 6 12 Q6 8 12 8 Q18 8 18 12 Q22 12 22 16 Q22 20 18 20 Z" fill="white" opacity="0.6" />
    </g>"""
    elif icon_name == "rain":
        return f"""<g transform="translate({x},{y})">
      <path d="M6 16 Q2 16 2 12 Q2 8 6 8 Q6 4 12 4 Q18 4 18 8 Q22 8 22 12 Q22 16 18 16 Z" fill="white" opacity="0.5" />
      <line x1="8" y1="18" x2="6" y2="22" stroke="#4fc3f7" stroke-width="1.5" stroke-linecap="round" />
      <line x1="13" y1="18" x2="11" y2="22" stroke="#4fc3f7" stroke-width="1.5" stroke-linecap="round" />
      <line x1="18" y1="18" x2="16" y2="22" stroke="#4fc3f7" stroke-width="1.5" stroke-linecap="round" />
    </g>"""
    elif icon_name == "snow":
        return f"""<g transform="translate({x},{y})">
      <path d="M6 14 Q2 14 2 10 Q2 6 6 6 Q6 2 12 2 Q18 2 18 6 Q22 6 22 10 Q22 14 18 14 Z" fill="white" opacity="0.6" />
      <circle cx="8" cy="18" r="1.5" fill="#e3f2fd" />
      <circle cx="13" cy="20" r="1.5" fill="#e3f2fd" />
      <circle cx="18" cy="17" r="1.5" fill="#e3f2fd" />
    </g>"""
    elif icon_name == "thunder":
        return f"""<g transform="translate({x},{y})">
      <path d="M6 14 Q2 14 2 10 Q2 6 6 6 Q6 2 12 2 Q18 2 18 6 Q22 6 22 10 Q22 14 18 14 Z" fill="white" opacity="0.5" />
      <polygon points="13,14 10,20 14,20 11,24" fill="{color}" />
    </g>"""
    elif icon_name == "fog":
        return f"""<g transform="translate({x},{y})">
      <line x1="4" y1="8" x2="20" y2="8" stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.5" />
      <line x1="6" y1="13" x2="18" y2="13" stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.4" />
      <line x1="4" y1="18" x2="20" y2="18" stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.3" />
    </g>"""
    else:
        # Default: cloud
        return f"""<g transform="translate({x},{y})">
      <path d="M6 20 Q2 20 2 16 Q2 12 6 12 Q6 8 12 8 Q18 8 18 12 Q22 12 22 16 Q22 20 18 20 Z" fill="white" opacity="0.5" />
    </g>"""


class CommitBadge:
    """Generate a commit count badge with sparkline graph."""

    @staticmethod
    def generate(
        username: str,
        commit_count: int,
        contribution_data: Optional[List[int]] = None,
        theme: str = "default",
        is_pro_user: bool = False,
        custom_colors: Optional[dict] = None,
    ) -> str:
        """Generate commit badge SVG."""
        t = _apply_custom_colors(get_theme(theme), custom_colors or {})

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

        # Commit icon (simple git commit dot) — no emoji
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
        custom_colors: Optional[dict] = None,
    ) -> str:
        """Generate language badge SVG."""
        t = _apply_custom_colors(get_theme(theme), custom_colors or {})

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
        custom_colors: Optional[dict] = None,
    ) -> str:
        """Generate activity badge SVG."""
        t = _apply_custom_colors(get_theme(theme), custom_colors or {})

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
        custom_colors: Optional[dict] = None,
    ) -> str:
        """Generate stats badge SVG."""
        t = _apply_custom_colors(get_theme(theme), custom_colors or {})

        width = 340
        height = 100

        def fmt(n: int) -> str:
            if n >= 1000000:
                return f"{n / 1000000:.1f}M"
            if n >= 1000:
                return f"{n / 1000:.1f}k"
            return str(n)

        # Stats items with SVG icons instead of emoji
        stats = [
            ("Stars", fmt(stars), t.accent, "star"),
            ("Forks", fmt(forks), t.muted, "fork"),
            ("Repos", fmt(repos), t.accent, "repo"),
            ("Followers", fmt(followers), t.muted, "people"),
            ("PRs", fmt(prs), t.accent, "pr"),
            ("Issues", fmt(issues), t.muted, "issue"),
        ]

        items = ""
        col_width = 105
        row_height = 28
        start_y = 24

        for i, (label, value, color, _icon) in enumerate(stats):
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
        custom_colors: Optional[dict] = None,
    ) -> str:
        """Generate coffee badge SVG with proper coffee cup icon."""
        t = _apply_custom_colors(get_theme(theme), custom_colors or {})

        width = 220
        height = 50

        # Coffee cup icon — SVG only, no emoji
        cup = _svg_icon_coffee(14, 12, t.accent)

        label = f"{username} bought" if username else "Coffees bought"
        content = f"""  {cup}
  <text x="48" y="22" font-family="Arial, sans-serif" font-size="11" fill="{t.muted}">{_escape(label)}</text>
  <text x="48" y="40" font-family="'Courier New', monospace" font-size="16" font-weight="700" fill="{t.accent}">{_escape(str(coffee_count))} cups</text>
  {_watermark(is_pro_user, height - 4)}"""

        return _svg_wrapper(width, height, content, t)


class SpotifyBadge:
    """Generate a now-playing Spotify badge (Pro only).

    Supports real Spotify API integration via SPOTIFY_TOKEN env var.
    If no token is configured, shows a static "Listening on Spotify" badge.
    """

    @staticmethod
    def generate(
        song: str = "Not playing",
        artist: str = "--",
        is_playing: bool = False,
        username: str = "",
        theme: str = "default",
        is_pro_user: bool = False,
        custom_colors: Optional[dict] = None,
    ) -> str:
        """Generate Spotify now-playing badge SVG."""
        t = _apply_custom_colors(get_theme(theme), custom_colors or {})

        width = 280
        height = 50

        # Spotify icon — SVG only
        icon = _svg_icon_spotify(10, 8, "#1DB954")

        # Status indicator
        status = "Now Playing" if is_playing else "Last Played"

        # Truncate long text
        song_display = song[:28] + "..." if len(song) > 28 else song
        artist_display = artist[:24] + "..." if len(artist) > 24 else artist

        # Playing animation (SMIL) for the dot indicator
        play_indicator = ""
        if is_playing:
            play_indicator = """<circle cx="40" cy="14" r="3" fill="#1DB954">
    <animate attributeName="opacity" values="1;0.4;1" dur="1.5s" repeatCount="indefinite" />
  </circle>"""

        content = f"""  {icon}
  {play_indicator}
  <text x="46" y="16" font-family="Arial, sans-serif" font-size="8" fill="#1DB954" opacity="0.8">{_escape(status)}</text>
  <text x="46" y="30" font-family="Arial, sans-serif" font-size="11" font-weight="600" fill="{t.foreground}">{_escape(song_display)}</text>
  <text x="46" y="44" font-family="Arial, sans-serif" font-size="10" fill="{t.muted}">{_escape(artist_display)}</text>
  {_watermark(is_pro_user, height - 4)}"""

        return _svg_wrapper(width, height, content, t)


class WeatherBadge:
    """Generate a current weather badge (Pro only).

    Fetches real weather data via wttr.in API (no API key needed).
    Set DEVBADGE_WEATHER_CITY env var or pass location parameter.
    """

    @staticmethod
    def generate(
        temp: str = "--",
        condition: str = "Unknown",
        location: str = "",
        icon_svg: str = "sun",
        theme: str = "default",
        is_pro_user: bool = False,
        custom_colors: Optional[dict] = None,
    ) -> str:
        """Generate weather badge SVG with proper weather icon."""
        t = _apply_custom_colors(get_theme(theme), custom_colors or {})

        width = 220
        height = 50

        # Weather icon — SVG only, no emoji
        icon = _svg_weather_icon(icon_svg, 12, 8, t.accent)

        # Location + condition display
        loc_text = location if location else condition
        cond_text = f"{condition}" if location else ""

        content = f"""  {icon}
  <text x="46" y="22" font-family="'Courier New', monospace" font-size="16" font-weight="700" fill="{t.accent}">{_escape(temp)}</text>
  <text x="46" y="38" font-family="Arial, sans-serif" font-size="10" fill="{t.muted}">{_escape(loc_text)}{(' - ' + _escape(cond_text)) if cond_text and cond_text != loc_text else ''}</text>
  {_watermark(is_pro_user, height - 4)}"""

        return _svg_wrapper(width, height, content, t)


class ProfileBadge:
    """Generate a profile overview badge."""

    @staticmethod
    def generate(
        name: str = "User",
        bio: str = "",
        repos: int = 0,
        followers: int = 0,
        age_days: int = 0,
        theme: str = "default",
        is_pro_user: bool = False,
        custom_colors: Optional[dict] = None,
    ) -> str:
        """Generate profile badge SVG — no emoji, SVG icons only."""
        t = _apply_custom_colors(get_theme(theme), custom_colors or {})

        width = 340
        height = 80
        age_years = age_days // 365

        # Small SVG icons for each stat
        repo_icon = _svg_icon_repo(18, 48, 8, t.muted)
        people_icon = _svg_icon_people(108, 48, 8, t.muted)
        # Calendar icon for age
        cal_icon = f"""<g transform="translate(198, 48)">
    <rect x="0" y="2" width="8" height="7" rx="1" fill="none" stroke="{t.muted}" stroke-width="1" />
    <line x1="2" y1="0" x2="2" y2="3" stroke="{t.muted}" stroke-width="1" />
    <line x1="6" y1="0" x2="6" y2="3" stroke="{t.muted}" stroke-width="1" />
  </g>"""

        bio_text = ""
        if bio:
            bio_display = bio[:50] + "..." if len(bio) > 50 else bio
            bio_text = f"""
  <text x="170" y="36" font-family="Arial, sans-serif" font-size="10" fill="{t.muted}" text-anchor="middle">{_escape(bio_display)}</text>"""

        content = f"""  <text x="170" y="20" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="{t.title_color}" text-anchor="middle">{_escape(name)}</text>{bio_text}
  {repo_icon}<text x="30" y="58" font-family="Arial, sans-serif" font-size="10" fill="{t.muted}">{repos} repos</text>
  {people_icon}<text x="120" y="58" font-family="Arial, sans-serif" font-size="10" fill="{t.muted}">{followers} followers</text>
  {cal_icon}<text x="210" y="58" font-family="Arial, sans-serif" font-size="10" fill="{t.muted}">{age_years}y on GitHub</text>
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

    Pro badges require a valid license key set via LICENSE_KEY env var
    or devbadge pro activate command.

    Custom colors from config are automatically applied.

    Args:
        badge_type: One of 'commits', 'languages', 'stats', 'activity',
                    'profile', 'coffee', 'spotify', 'weather'.
        stats: UserStats object (from github_stats).
        theme: Theme name.
        is_pro_user: Deprecated — Pro status is now verified via license.
        **kwargs: Additional parameters for specific badge types.

    Returns:
        SVG string.
    """
    # Always verify Pro status through the license system.
    verified_pro = is_pro()

    # Load custom colors from config
    config = DevBadgeConfig.load()
    custom_colors = kwargs.pop("custom_colors", None) or config.custom_colors

    # Check if Pro badge is requested without a verified license
    if badge_type in PRO_BADGES and not verified_pro:
        return _pro_required_badge(badge_type, theme, custom_colors)

    # Use verified status for all downstream checks
    is_pro_user = verified_pro

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

    return generator(stats=stats, theme=theme, is_pro_user=is_pro_user,
                     custom_colors=custom_colors, **kwargs)


def _gen_commits(stats, theme, is_pro_user, custom_colors=None, **kwargs) -> str:
    """Generate commit badge from stats."""
    if stats:
        return CommitBadge.generate(
            username=stats.username,
            commit_count=stats.total_commits,
            contribution_data=stats.contribution_data,
            theme=theme,
            is_pro_user=is_pro_user,
            custom_colors=custom_colors,
        )
    return CommitBadge.generate(
        username=kwargs.get("username", "user"),
        commit_count=kwargs.get("commit_count", 0),
        contribution_data=kwargs.get("contribution_data"),
        theme=theme,
        is_pro_user=is_pro_user,
        custom_colors=custom_colors,
    )


def _gen_languages(stats, theme, is_pro_user, custom_colors=None, **kwargs) -> str:
    """Generate language badge from stats."""
    if stats and stats.languages:
        langs = [{"name": l.name, "bytes": l.bytes, "color": l.color} for l in stats.languages]
    else:
        langs = kwargs.get("languages", [])
    return LanguageBadge.generate(languages=langs, theme=theme, is_pro_user=is_pro_user,
                                 custom_colors=custom_colors)


def _gen_stats(stats, theme, is_pro_user, custom_colors=None, **kwargs) -> str:
    """Generate stats badge."""
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
            custom_colors=custom_colors,
        )
    return StatsBadge.generate(theme=theme, is_pro_user=is_pro_user,
                               custom_colors=custom_colors, **filtered)


def _gen_activity(stats, theme, is_pro_user, custom_colors=None, **kwargs) -> str:
    """Generate activity badge."""
    if stats:
        return ActivityBadge.generate(
            contribution_data=stats.contribution_data,
            theme=theme,
            is_pro_user=is_pro_user,
            custom_colors=custom_colors,
        )
    return ActivityBadge.generate(
        contribution_data=kwargs.get("contribution_data"),
        theme=theme,
        is_pro_user=is_pro_user,
        custom_colors=custom_colors,
    )


def _gen_profile(stats, theme, is_pro_user, custom_colors=None, **kwargs) -> str:
    """Generate a profile overview badge."""
    if stats:
        return ProfileBadge.generate(
            name=stats.name or stats.username,
            bio=stats.bio,
            repos=stats.public_repos,
            followers=stats.followers,
            age_days=stats.account_age_days,
            theme=theme,
            is_pro_user=is_pro_user,
            custom_colors=custom_colors,
        )
    return ProfileBadge.generate(
        name=kwargs.get("username", "User"),
        bio=kwargs.get("bio", ""),
        repos=kwargs.get("repos", 0),
        followers=kwargs.get("followers", 0),
        age_days=kwargs.get("age_days", 0),
        theme=theme,
        is_pro_user=is_pro_user,
        custom_colors=custom_colors,
    )


def _gen_coffee(stats, theme, is_pro_user, custom_colors=None, **kwargs) -> str:
    """Generate coffee badge."""
    return CoffeeBadge.generate(
        coffee_count=kwargs.get("coffee_count", 0),
        username=kwargs.get("username", ""),
        theme=theme,
        is_pro_user=is_pro_user,
        custom_colors=custom_colors,
    )


def _gen_spotify(stats, theme, is_pro_user, custom_colors=None, **kwargs) -> str:
    """Generate Spotify badge with real API data if available."""
    # Try to fetch real Spotify data
    song = kwargs.get("song", "")
    artist = kwargs.get("artist", "")
    is_playing = kwargs.get("is_playing", False)

    if not song:
        # Try to fetch from Spotify API
        config = DevBadgeConfig.load()
        spotify_token = kwargs.get("spotify_token", "") or config.spotify_token

        if spotify_token:
            try:
                from devbadge.github_stats import fetch_spotify_now_playing
                spotify_data = fetch_spotify_now_playing(spotify_token)
                song = spotify_data.get("song", "Not playing")
                artist = spotify_data.get("artist", "--")
                is_playing = spotify_data.get("is_playing", False)
            except Exception:
                song = "Not playing"
                artist = "--"
        else:
            song = "Not configured"
            artist = "Set SPOTIFY_TOKEN"

    return SpotifyBadge.generate(
        song=song,
        artist=artist,
        is_playing=is_playing,
        theme=theme,
        is_pro_user=is_pro_user,
        custom_colors=custom_colors,
    )


def _gen_weather(stats, theme, is_pro_user, custom_colors=None, **kwargs) -> str:
    """Generate weather badge with real wttr.in data if available."""
    temp = kwargs.get("temp", "")
    condition = kwargs.get("condition", "")
    location = kwargs.get("location", "")
    icon_svg = kwargs.get("icon_svg", "sun")

    if not temp:
        # Try to fetch real weather data
        config = DevBadgeConfig.load()
        city = kwargs.get("city", "") or config.weather_city

        if city:
            try:
                from devbadge.github_stats import fetch_weather
                weather_data = fetch_weather(city)
                temp = weather_data.get("temp", "--")
                condition = weather_data.get("condition", "Unknown")
                location = weather_data.get("location", city)
                icon_svg = weather_data.get("icon_svg", "cloud")
            except Exception:
                temp = "--"
                condition = "N/A"
                location = city
        else:
            temp = "--"
            condition = "Set DEVBADGE_WEATHER_CITY"
            location = ""

    return WeatherBadge.generate(
        temp=temp,
        condition=condition,
        location=location,
        icon_svg=icon_svg,
        theme=theme,
        is_pro_user=is_pro_user,
        custom_colors=custom_colors,
    )


def _pro_required_badge(badge_type: str, theme: str = "default",
                        custom_colors: Optional[dict] = None) -> str:
    """Generate a 'Pro required' placeholder badge."""
    t = _apply_custom_colors(get_theme(theme), custom_colors or {})
    width = 220
    height = 36

    # Lock icon SVG — no emoji
    lock = f"""<g transform="translate(80, 8)">
    <rect x="3" y="10" width="12" height="10" rx="2" fill="{t.muted}" />
    <path d="M6 10 V7 Q6 3 9 3 Q12 3 12 7 V10" fill="none" stroke="{t.muted}" stroke-width="1.5" />
  </g>"""

    content = f"""  {lock}
  <text x="100" y="22" font-family="Arial, sans-serif" font-size="11" fill="{t.muted}" text-anchor="middle">{_escape(badge_type.title())} - Pro only</text>
  {_watermark(False, height - 4)}"""

    return _svg_wrapper(width, height, content, t)
