<div align="center">

# DevBadge

**Dynamic SVG badges for GitHub profiles**

Generate beautiful, customizable badges that showcase your GitHub stats, languages, activity, and more — all in pure SVG with no emoji dependencies.

[![PyPI version](https://img.shields.io/pypi/v/devbadge?color=415a77)](https://pypi.org/project/devbadge/)
[![Python](https://img.shields.io/pypi/pyversions/devbadge?color=415a77)](https://pypi.org/project/devbadge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-415a77.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Buy_Pro-@allstarspay_bot-f0883e)](https://t.me/allstarspay_bot)

</div>

---

## Demo

### Commit Badge
<img src="https://raw.githubusercontent.com/sochiautoparts/devbadge/main/badges/commits.svg" alt="Commits" />

### Language Badge
<img src="https://raw.githubusercontent.com/sochiautoparts/devbadge/main/badges/languages.svg" alt="Languages" />

### Stats Badge
<img src="https://raw.githubusercontent.com/sochiautoparts/devbadge/main/badges/stats.svg" alt="Stats" />

### Activity Badge
<img src="https://raw.githubusercontent.com/sochiautoparts/devbadge/main/badges/activity.svg" alt="Activity" />

---

## Installation

```bash
pip install devbadge
```

Or install from source:

```bash
git clone https://github.com/sochiautoparts/devbadge.git
cd devbadge
pip install -e .
```

---

## Usage

### CLI

```bash
# Generate specific badges
devbadge generate --user octocat --badge commits --theme dracula

# Generate all free badges
devbadge generate --user octocat --all --theme github-dark

# Generate with output directory
devbadge generate --user octocat --all --output ./my-badges/

# Generate with custom colors (Pro)
devbadge generate --user octocat --all --color accent=#ff0000 --color background=#111111

# Weather badge with city (Pro)
devbadge generate --user octocat --badge weather --city "San Francisco"

# Spotify now-playing badge (Pro)
devbadge generate --user octocat --badge spotify --spotify-token "your_oauth_token"

# Initialize config file
devbadge init

# Check Pro license status
devbadge pro status

# Activate Pro license
devbadge pro activate SP-DVB-xxxx-xxxx

# List available themes
devbadge themes
```

### Python API

```python
from devbadge import generate_badge, get_theme
from devbadge.github_stats import fetch_stats

# Fetch GitHub stats
stats = fetch_stats("octocat", token="ghp_xxxx")

# Generate a commit badge
svg = generate_badge("commits", stats=stats, theme="dracula")

# Save to file
with open("commits.svg", "w") as f:
    f.write(svg)

# Generate all badges
for badge_type in ["commits", "languages", "stats", "activity", "profile"]:
    svg = generate_badge(badge_type, stats=stats, theme="nord")
    with open(f"{badge_type}.svg", "w") as f:
        f.write(svg)
```

### Pro Features

```python
from devbadge import generate_badge
from devbadge.config import is_pro

# Pro badges (require license key)
if is_pro("SP-DVB-xxxx-xxxx"):
    # Coffee badge with SVG icon (no emoji)
    svg = generate_badge("coffee", is_pro_user=True, username="dev", coffee_count=5)

    # Spotify now-playing (real API via SPOTIFY_TOKEN env var)
    svg = generate_badge("spotify", is_pro_user=True, spotify_token="your_token")

    # Weather badge (real wttr.in API, no API key needed)
    svg = generate_badge("weather", is_pro_user=True, city="Tokyo")

# Custom colors (Pro)
svg = generate_badge("stats", stats=stats, is_pro_user=True,
                     custom_colors={"accent": "#ff6600", "background": "#1a1a2e"})

# SMIL animations that work on GitHub (Pro only)
from devbadge.animations import apply_animation
svg = generate_badge("stats", stats=stats, is_pro_user=True)
svg = apply_animation(svg, "pulse", "stats-1", is_pro=True, color="#58a6ff")
svg = apply_animation(svg, "sparkle", "stars-1", is_pro=True, count=3)
```

> **Note:** All animations use SMIL (`<animate>`, `<animateTransform>`) which GitHub DOES support in SVGs. No CSS `<style>` tags are used.

---

## GitHub Action

Add this to `.github/workflows/update-badges.yml`:

```yaml
name: Update Badges

on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - name: Generate Badges
        uses: sochiautoparts/devbadge@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          badges: 'commits,languages,stats,activity'
          theme: 'dracula'
          output-dir: './badges'
          license-key: ${{ secrets.DEVBADGE_LICENSE }}
```

---

## Themes

| Theme | Preview | Pro Only |
|-------|---------|----------|
| `default` | Dark blue | No |
| `dracula` | Dracula purple | No |
| `github-dark` | GitHub Dark | No |
| `solarized` | Solarized Dark | No |
| `nord` | Nord palette | No |
| `monokai` | Monokai green | No |
| `neon` | Neon glow | Yes |
| `aurora` | Aurora gradient | Yes |

```bash
# Use a theme
devbadge generate --user octocat --theme nord --all

# Pro themes require license
devbadge generate --user octocat --theme neon --all --license SP-DVB-xxxx-xxxx
```

---

## Badge Types

| Badge | Type | Free | Pro |
|-------|------|------|-----|
| Commits | `commits` | Yes | Yes |
| Languages | `languages` | Yes | Yes |
| Stats | `stats` | Yes | Yes |
| Activity | `activity` | Yes | Yes |
| Profile | `profile` | Yes | Yes |
| Coffee | `coffee` | Locked | Yes |
| Spotify | `spotify` | Locked | Yes |
| Weather | `weather` | Locked | Yes |

### Pro Badge Details

- **Coffee**: SVG coffee cup icon + count. No emoji, renders everywhere.
- **Spotify**: Real now-playing via Spotify API (set `SPOTIFY_TOKEN`). Falls back to "Not configured".
- **Weather**: Real weather via wttr.in API (set `DEVBADGE_WEATHER_CITY` or use `--city`). No API key needed.

---

## Free vs Pro

| Feature | Free | Pro |
|---------|------|-----|
| Basic badges (5 types) | Yes | Yes |
| Pro badges (3 types) | Locked | Yes |
| Themes (6 free) | Yes | Yes |
| Pro themes (2) | Locked | Yes |
| SMIL animations | Locked | Yes |
| Custom colors | Locked | Yes |
| No watermark | Locked | Yes |
| Rate-limited API | Yes | Yes |

---

## Pro Version & Pricing

### Prices

| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0 forever | 5 basic badges, 6 themes, with watermark |
| **Pro Monthly** | 149 stars/mo | All badges + animations + themes + no watermark |
| **Pro Yearly** | 999 stars/yr | Everything in Pro + 44% savings |
| **Pro Lifetime** | 2999 stars forever | Everything in Pro + lifetime access + early features |

### How to Buy

1. Open bot [@allstarspay_bot](https://t.me/allstarspay_bot) in Telegram
2. Select **DevBadge Pro** product
3. Pay with the selected plan
4. Receive a license key in format `SP-DVB-xxxx-xxxx`
5. Activate the key:

```bash
devbadge pro activate SP-DVB-xxxx-xxxx
```

Or via environment variable:

```bash
export LICENSE_KEY=SP-DVB-xxxx-xxxx
devbadge generate --user octocat --all
```

---

## License Verification

DevBadge Pro uses a multi-layer license verification system with HMAC-signed cache:

1. **Local Cache** — HMAC-signed cache in `~/.devbadge/license_cache.json` (offline capable, 24h re-verification)
2. **Public Registry** — Checks `licenses.json` from [StarsPay Bot repo](https://github.com/sochiautoparts/stars-pay-bot)
3. **REST API Fallback** — Verifies via StarsPay API with `STARSPAY_API_KEY`

### Cache Security

Cache entries are signed with HMAC using a key derived from the license key. Manually creating cache files with `valid=true` will fail signature verification. Cache expires after 24 hours and must be re-verified with the server.

### Key Format

```
SP-DVB-xxxx-xxxx
|  |   |    |
|  |   |    +-- Unique suffix (4 chars)
|  |   +-- Product code (DVB = DevBadge)
|  +-- StarsPay prefix
+-- Service identifier
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `LICENSE_KEY` or `DEVBADGE_LICENSE` | Pro license key |
| `GITHUB_TOKEN` | GitHub personal access token |
| `SPOTIFY_TOKEN` | Spotify OAuth token (for now-playing badge) |
| `DEVBADGE_WEATHER_CITY` | Default city for weather badge |
| `STARSPAY_API_KEY` | StarsPay API key (for REST fallback) |
| `DEVBADGE_THEME` | Default theme |
| `DEVBADGE_OUTPUT` | Default output directory |

---

## Technical Details

### SVG Rendering

All badges use pure SVG with no emoji characters. Emoji in `<text>` elements don't render reliably across platforms, so we use:
- SVG shape icons (circles, polygons, paths) for visual elements
- Plain text labels for stat names
- SMIL `<animate>` for animations (GitHub-compatible)

### Commit Count

DevBadge fetches **lifetime** commit counts by summing `contributionsCollection` across all years from the user's account creation date. This provides accurate total commit counts, not just the current year.

### API Rate Limiting

GitHub API calls are cached in memory for 5 minutes to respect rate limits. When rate-limited, the tool automatically waits (up to 60s) and retries.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/sochiautoparts/devbadge.git
cd devbadge
pip install -e ".[dev]"
pytest tests/ -v
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**[Get DevBadge Pro](https://t.me/allstarspay_bot)** · **[Documentation](https://sochiautoparts.github.io/devbadge/)** · **[Report Bug](https://github.com/sochiautoparts/devbadge/issues)**

Made with care by [sochiautoparts](https://github.com/sochiautoparts)

</div>
