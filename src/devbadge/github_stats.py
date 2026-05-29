"""Fetch GitHub statistics via the REST/GraphQL API."""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore


@dataclass
class LanguageStat:
    """A single language with byte count."""

    name: str
    bytes: int
    color: str = "#555555"


@dataclass
class UserStats:
    """Aggregated GitHub statistics for a user."""

    username: str
    name: str = ""
    bio: str = ""
    avatar_url: str = ""
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    total_stars: int = 0
    total_forks: int = 0
    total_commits: int = 0
    total_prs: int = 0
    total_issues: int = 0
    languages: List[LanguageStat] = field(default_factory=list)
    account_age_days: int = 0
    created_at: str = ""
    contribution_data: List[int] = field(default_factory=list)  # last 52 weeks, 7 days each


GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"

# Simple in-memory cache for API responses to respect rate limits
_api_cache: Dict[str, tuple] = {}  # url -> (timestamp, data)
_CACHE_TTL = 300  # 5 minutes


def _get_cached(url: str) -> Optional[Any]:
    """Get cached API response if still valid."""
    if url in _api_cache:
        ts, data = _api_cache[url]
        if time.time() - ts < _CACHE_TTL:
            return data
        del _api_cache[url]
    return None


def _set_cached(url: str, data: Any) -> None:
    """Cache an API response."""
    _api_cache[url] = (time.time(), data)
    # Limit cache size
    if len(_api_cache) > 100:
        oldest = min(_api_cache, key=lambda k: _api_cache[k][0])
        del _api_cache[oldest]


def _headers(token: Optional[str] = None) -> Dict[str, str]:
    """Build request headers."""
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(token: Optional[str], url: str, params: Optional[Dict] = None) -> Any:
    """Perform a GET request to GitHub API with caching and rate limit handling."""
    if httpx is None:
        raise RuntimeError("httpx is required for GitHub API access. Install with: pip install httpx")

    # Check cache first
    cache_key = f"{url}?{sorted(params.items()) if params else ''}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    with httpx.Client(timeout=30) as client:
        r = client.get(url, headers=_headers(token), params=params)

        # Handle rate limiting
        if r.status_code == 403 and "rate limit" in r.text.lower():
            reset_time = int(r.headers.get("X-RateLimit-Reset", 0))
            if reset_time:
                wait_time = max(reset_time - int(time.time()), 1)
                if wait_time <= 60:  # Only wait up to 60 seconds
                    time.sleep(wait_time + 1)
                    r = client.get(url, headers=_headers(token), params=params)
                else:
                    raise RuntimeError(f"GitHub API rate limit exceeded. Resets in {wait_time}s")
            else:
                raise RuntimeError("GitHub API rate limit exceeded")

        r.raise_for_status()
        data = r.json()
        _set_cached(cache_key, data)
        return data


def _post_graphql(token: Optional[str], query: str, variables: Optional[Dict] = None) -> Any:
    """Execute a GraphQL query."""
    if httpx is None:
        raise RuntimeError("httpx is required for GitHub API access. Install with: pip install httpx")
    with httpx.Client(timeout=30) as client:
        r = client.post(
            GITHUB_GRAPHQL,
            headers=_headers(token),
            json={"query": query, "variables": variables or {}},
        )
        r.raise_for_status()
        data = r.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL error: {data['errors']}")
        return data["data"]


def fetch_user_profile(username: str, token: Optional[str] = None) -> Dict:
    """Fetch basic user profile data."""
    return _get(token, f"{GITHUB_API}/users/{username}")


def fetch_user_repos(username: str, token: Optional[str] = None) -> List[Dict]:
    """Fetch all public repos for a user (paginated)."""
    repos = []
    page = 1
    while True:
        batch = _get(token, f"{GITHUB_API}/users/{username}/repos", params={
            "per_page": 100,
            "page": page,
            "type": "owner",
            "sort": "updated",
        })
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def fetch_repo_languages(repo_full_name: str, token: Optional[str] = None) -> Dict[str, int]:
    """Fetch language breakdown for a single repo."""
    return _get(token, f"{GITHUB_API}/repos/{repo_full_name}/languages")


def fetch_commit_count_graphql(username: str, token: Optional[str] = None) -> int:
    """Fetch total commit count via GraphQL by summing multiple years.

    The `contributionsCollection` defaults to the current year only.
    To get lifetime commits, we sum contributions across all years
    from the user's account creation date.

    Args:
        username: GitHub username.
        token: GitHub personal access token (required for GraphQL).

    Returns:
        Total commit count (lifetime), or 0 if unavailable.
    """
    # First, get the user's account creation date
    profile_query = """
    query($login: String!) {
      user(login: $login) {
        createdAt
      }
    }
    """
    try:
        data = _post_graphql(token, profile_query, {"login": username})
        created_at = data["user"]["createdAt"]
        created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except Exception:
        # Fallback: just use current year
        created_date = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    total_commits = 0

    # Sum contributions for each year from account creation
    current = datetime(created_date.year, 1, 1, tzinfo=timezone.utc)
    while current <= now:
        year_end = datetime(current.year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        # Clamp to now if the year is current
        if year_end > now:
            year_end = now
        # Clamp to creation date for the first year
        year_start = max(current, created_date)

        year_query = """
        query($login: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $login) {
            contributionsCollection(from: $from, to: $to) {
              totalCommitContributions
              restrictedContributionsCount
            }
          }
        }
        """
        try:
            data = _post_graphql(token, year_query, {
                "login": username,
                "from": year_start.isoformat(),
                "to": year_end.isoformat(),
            })
            collection = data["user"]["contributionsCollection"]
            total_commits += collection["totalCommitContributions"] + collection["restrictedContributionsCount"]
        except Exception:
            pass  # Skip this year on error

        # Move to next year
        current = datetime(current.year + 1, 1, 1, tzinfo=timezone.utc)

    return total_commits


def fetch_contribution_calendar(username: str, token: Optional[str] = None) -> List[int]:
    """Fetch contribution data for the last year (52 weeks x 7 days).

    Returns a flat list of 364 integers (contribution counts per day).
    """
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    try:
        data = _post_graphql(token, query, {"login": username})
        weeks = data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        counts = []
        for week in weeks:
            for day in week["contributionDays"]:
                counts.append(day["contributionCount"])
        return counts
    except Exception:
        # Fallback: return zeros
        return [0] * 364


def aggregate_languages(repos: List[Dict], username: str, token: Optional[str] = None) -> List[LanguageStat]:
    """Aggregate language stats across all repos."""
    from devbadge.themes import LANGUAGE_COLORS

    lang_totals: Dict[str, int] = {}
    for repo in repos:
        full_name = repo.get("full_name", "")
        if not full_name:
            continue
        try:
            langs = fetch_repo_languages(full_name, token)
            for lang, byte_count in langs.items():
                lang_totals[lang] = lang_totals.get(lang, 0) + byte_count
        except Exception:
            continue

    # Sort by byte count descending
    sorted_langs = sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)

    result = []
    for lang, byte_count in sorted_langs[:10]:  # Top 10 languages
        result.append(LanguageStat(
            name=lang,
            bytes=byte_count,
            color=LANGUAGE_COLORS.get(lang, "#555555"),
        ))
    return result


def fetch_weather(city: str) -> Dict[str, str]:
    """Fetch current weather for a city via wttr.in API.

    No API key required. Returns dict with temp, condition, location.
    """
    if httpx is None:
        return {"temp": "--", "condition": "N/A", "location": city}

    try:
        # wttr.in JSON format
        url = f"https://wttr.in/{city}?format=j1"
        with httpx.Client(timeout=10) as client:
            r = client.get(url, headers={"Accept": "application/json"})
            r.raise_for_status()
            data = r.json()

        current = data.get("current_condition", [{}])[0]
        temp_c = current.get("temp_C", "--")
        condition = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
        area = data.get("nearest_area", [{}])[0]
        location = area.get("areaName", [{}])[0].get("value", city)

        # Weather condition to icon mapping
        weather_code = current.get("weatherCode", "113")
        icon = _weather_code_to_svg_icon(weather_code)

        return {
            "temp": f"{temp_c}°C",
            "condition": condition,
            "location": location,
            "icon_code": weather_code,
            "icon_svg": icon,
        }
    except Exception:
        return {"temp": "--", "condition": "N/A", "location": city, "icon_code": "113", "icon_svg": "sun"}


def _weather_code_to_svg_icon(code: str) -> str:
    """Map wttr.in weather code to SVG icon name."""
    code_int = int(code)
    if code_int in (113,):
        return "sun"
    elif code_int in (116,):
        return "cloud-sun"
    elif code_int in (119, 122):
        return "cloud"
    elif code_int in (176, 263, 266, 293, 296, 299, 302, 305, 308, 311, 314, 317, 353, 356, 359):
        return "rain"
    elif code_int in (179, 182, 185, 227, 230, 320, 323, 326, 329, 332, 335, 338, 350, 362, 365, 368, 371, 374, 377, 392, 395):
        return "snow"
    elif code_int in (200, 386, 389):
        return "thunder"
    elif code_int in (143, 248, 260):
        return "fog"
    else:
        return "cloud"


def fetch_spotify_now_playing(access_token: str) -> Dict[str, str]:
    """Fetch currently playing track from Spotify API.

    Args:
        access_token: Spotify OAuth access token.

    Returns:
        Dict with song, artist, is_playing fields.
    """
    if not access_token:
        return {"song": "Not configured", "artist": "Set SPOTIFY_TOKEN", "is_playing": False}

    if httpx is None:
        return {"song": "Not playing", "artist": "--", "is_playing": False}

    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(
                "https://api.spotify.com/v1/me/player/currently-playing",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if r.status_code == 204:
                # No track currently playing — get last played
                r2 = client.get(
                    "https://api.spotify.com/v1/me/player/recently-played?limit=1",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if r2.status_code == 200:
                    data = r2.json()
                    items = data.get("items", [])
                    if items:
                        track = items[0].get("track", {})
                        song = track.get("name", "Unknown")
                        artists = track.get("artists", [])
                        artist = artists[0].get("name", "Unknown") if artists else "Unknown"
                        return {"song": song, "artist": artist, "is_playing": False}
                return {"song": "Not playing", "artist": "--", "is_playing": False}

            if r.status_code == 401:
                return {"song": "Token expired", "artist": "Refresh SPOTIFY_TOKEN", "is_playing": False}

            r.raise_for_status()
            data = r.json()

            if not data.get("is_playing", False) and data.get("item"):
                track = data["item"]
                song = track.get("name", "Unknown")
                artists = track.get("artists", [])
                artist = artists[0].get("name", "Unknown") if artists else "Unknown"
                return {"song": song, "artist": artist, "is_playing": False}

            if data.get("item"):
                track = data["item"]
                song = track.get("name", "Unknown")
                artists = track.get("artists", [])
                artist = artists[0].get("name", "Unknown") if artists else "Unknown"
                return {"song": song, "artist": artist, "is_playing": True}

            return {"song": "Not playing", "artist": "--", "is_playing": False}
    except Exception:
        return {"song": "Not playing", "artist": "--", "is_playing": False}


def fetch_stats(username: str, token: Optional[str] = None) -> UserStats:
    """Fetch comprehensive GitHub stats for a user.

    Args:
        username: GitHub username.
        token: Optional GitHub personal access token (increases rate limit).

    Returns:
        UserStats with aggregated data.
    """
    profile = fetch_user_profile(username, token)
    repos = fetch_user_repos(username, token)

    # Basic profile
    stats = UserStats(
        username=username,
        name=profile.get("name") or username,
        bio=profile.get("bio") or "",
        avatar_url=profile.get("avatar_url", ""),
        public_repos=profile.get("public_repos", 0),
        followers=profile.get("followers", 0),
        following=profile.get("following", 0),
        created_at=profile.get("created_at", ""),
    )

    # Account age
    if stats.created_at:
        try:
            created = datetime.fromisoformat(stats.created_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            stats.account_age_days = (now - created).days
        except (ValueError, TypeError):
            pass

    # Aggregate stars and forks from repos
    stats.total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    stats.total_forks = sum(r.get("forks_count", 0) for r in repos)

    # Try GraphQL for lifetime commit count
    if token:
        stats.total_commits = fetch_commit_count_graphql(username, token)
        stats.contribution_data = fetch_contribution_calendar(username, token)

        # PR and issue counts via search
        try:
            pr_result = _get(token, f"{GITHUB_API}/search/issues", params={
                "q": f"author:{username} type:pr is:merged",
                "per_page": 1,
            })
            stats.total_prs = pr_result.get("total_count", 0)
        except Exception:
            pass

        try:
            issue_result = _get(token, f"{GITHUB_API}/search/issues", params={
                "q": f"author:{username} type:issue",
                "per_page": 1,
            })
            stats.total_issues = issue_result.get("total_count", 0)
        except Exception:
            pass
    else:
        # No token — use commit count from public repos via Link header
        # GitHub REST API returns a Link header with last page number = total commits
        total = 0
        for repo in repos[:10]:
            try:
                full_name = repo.get("full_name", "")
                if not full_name:
                    continue
                with httpx.Client(timeout=10) as client:
                    r = client.get(
                        f"{GITHUB_API}/repos/{full_name}/commits?per_page=1",
                        headers={"Accept": "application/vnd.github+json"},
                    )
                    # Parse Link header for last page number (= total commits)
                    link_header = r.headers.get("Link", "")
                    if 'rel="last"' in link_header:
                        match = re.search(r'page=(\d+)>; rel="last"', link_header)
                        if match:
                            total += int(match.group(1))
                            continue
                    # Fallback: count results in response
                    if r.status_code == 200:
                        data = r.json()
                        total += len(data) if isinstance(data, list) else 0
            except Exception:
                continue
        stats.total_commits = total

    # Languages
    stats.languages = aggregate_languages(repos, username, token)

    return stats
