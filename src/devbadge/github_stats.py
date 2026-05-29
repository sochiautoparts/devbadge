"""Fetch GitHub statistics via the REST/GraphQL API."""

from __future__ import annotations

import os
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
    """Perform a GET request to GitHub API."""
    if httpx is None:
        raise RuntimeError("httpx is required for GitHub API access. Install with: pip install httpx")
    with httpx.Client(timeout=30) as client:
        r = client.get(url, headers=_headers(token), params=params)
        r.raise_for_status()
        return r.json()


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
    """Fetch total commit count via GraphQL contributions_collection."""
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
        }
      }
    }
    """
    try:
        data = _post_graphql(token, query, {"login": username})
        collection = data["user"]["contributionsCollection"]
        return collection["totalCommitContributions"] + collection["restrictedContributionsCount"]
    except Exception:
        return 0


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

    # Try GraphQL for commit count
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
        import re
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
