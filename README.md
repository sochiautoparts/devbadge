<div align="center">

# 🏅 DevBadge

**Dynamic SVG badges for GitHub profiles**

Generate beautiful, customizable badges that showcase your GitHub stats, languages, activity, and more — all in pure SVG.

[![PyPI version](https://img.shields.io/pypi/v/devbadge?color=415a77)](https://pypi.org/project/devbadge/)
[![Python](https://img.shields.io/pypi/pyversions/devbadge?color=415a77)](https://pypi.org/project/devbadge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-415a77.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Buy_Pro-@allstarspay_bot-f0883e)](https://t.me/allstarspay_bot)

</div>

---

## ✨ Demo

### Commit Badge
<img src="https://raw.githubusercontent.com/sochiautoparts/devbadge/main/badges/commits.svg" alt="Commits" />

<details>
<summary>📝 SVG Preview</summary>

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="340" height="50" viewBox="0 0 340 50">
  <rect width="340" height="50" rx="6" fill="#0d1b2a" />
  <rect x="0.5" y="0.5" width="339" height="49" rx="5.5" fill="none" stroke="#415a77" stroke-width="1" opacity="0.3" />
  <text x="42" y="22" font-family="Arial, sans-serif" font-size="11" font-weight="600" fill="#e0e1dd">octocat's commits</text>
  <text x="42" y="40" font-family="'Courier New', monospace" font-size="18" font-weight="700" fill="#415a77">1,247</text>
  <circle cx="24" cy="25" r="6" fill="none" stroke="#415a77" stroke-width="2" />
  <circle cx="24" cy="25" r="2" fill="#415a77" />
  <line x1="24" y1="19" x2="24" y2="10" stroke="#415a77" stroke-width="2" />
  <line x1="24" y1="31" x2="24" y2="40" stroke="#415a77" stroke-width="2" />
  <polyline points="140,38 146,32 152,34 158,28 164,30 170,22 176,26 182,20 188,24 194,18 200,22 206,16 212,20 218,14 224,18 230,12 236,16 242,10 248,14 254,12 260,16 266,10 272,14 278,18 284,12 290,16 296,20 302,14 308,18 314,16 320,20" fill="none" stroke="#415a77" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.8" />
  <a href="https://github.com/sochiautoparts/devbadge" target="_blank">
    <text x="4" y="46" font-family="Arial, sans-serif" font-size="8" fill="#666666" opacity="0.6">DevBadge</text>
  </a>
</svg>
```

</details>

### Language Badge
<img src="https://raw.githubusercontent.com/sochiautoparts/devbadge/main/badges/languages.svg" alt="Languages" />

### Stats Badge
<img src="https://raw.githubusercontent.com/sochiautoparts/devbadge/main/badges/stats.svg" alt="Stats" />

### Activity Badge
<img src="https://raw.githubusercontent.com/sochiautoparts/devbadge/main/badges/activity.svg" alt="Activity" />

---

## 🚀 Installation

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

## 📖 Usage

### CLI

```bash
# Generate specific badges
devbadge generate --user octocat --badge commits --theme dracula

# Generate all free badges
devbadge generate --user octocat --all --theme github-dark

# Generate with output directory
devbadge generate --user octocat --all --output ./my-badges/

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
    svg = generate_badge("coffee", is_pro_user=True, username="dev", coffee_count=5)
    svg = generate_badge("spotify", is_pro_user=True, song="Bohemian Rhapsody", artist="Queen")
    svg = generate_badge("weather", is_pro_user=True, temp="22°C", condition="Sunny")

# Animated badges (Pro only)
from devbadge.animations import apply_animation
svg = generate_badge("stats", stats=stats, is_pro_user=True)
svg = apply_animation(svg, "pulse", "stats-1", is_pro=True, color="#58a6ff")
```

---

## 🤖 GitHub Action

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
```

Or run manually:

```yaml
- name: Install & Generate
  run: |
    pip install devbadge
    devbadge generate --user ${{ github.repository_owner }} --all --theme dracula --token ${{ secrets.GITHUB_TOKEN }} --output ./badges
```

---

## 🎨 Themes

| Theme | Preview | Pro Only |
|-------|---------|----------|
| `default` | Dark blue | ❌ |
| `dracula` | Dracula purple | ❌ |
| `github-dark` | GitHub Dark | ❌ |
| `solarized` | Solarized Dark | ❌ |
| `nord` | Nord palette | ❌ |
| `monokai` | Monokai green | ❌ |
| `neon` | Neon glow ⚡ | ⭐ Yes |
| `aurora` | Aurora gradient ⚡ | ⭐ Yes |

```bash
# Use a theme
devbadge generate --user octocat --theme nord --all

# Pro themes require license
devbadge generate --user octocat --theme neon --all --license SP-DVB-xxxx-xxxx
```

---

## 🏷️ Badge Types

| Badge | Type | Free | Pro |
|-------|------|------|-----|
| Commits | `commits` | ✅ | ✅ |
| Languages | `languages` | ✅ | ✅ |
| Stats | `stats` | ✅ | ✅ |
| Activity | `activity` | ✅ | ✅ |
| Profile | `profile` | ✅ | ✅ |
| Coffee | `coffee` | 🔒 | ✅ |
| Spotify | `spotify` | 🔒 | ✅ |
| Weather | `weather` | 🔒 | ✅ |

---

## 🆚 Free vs Pro

| Feature | Free | Pro ⭐ |
|---------|------|--------|
| Basic badges (5 types) | ✅ | ✅ |
| Pro badges (3 types) | 🔒 | ✅ |
| Themes (6) | ✅ | ✅ |
| Pro themes (2 animated) | 🔒 | ✅ |
| Animations | 🔒 | ✅ |
| No watermark | 🔒 | ✅ |
| Custom colors | 🔒 | ✅ |
| Priority support | 🔒 | ✅ |

---

## 💎 Pro Version & Оплата

### Цены / Pricing

| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0 навсегда | 5 базовых бейджей, 6 тем, с водяным знаком |
| **Pro Monthly** | ⭐149/мес | Все бейджи + анимации + темы + без водяного знака |
| **Pro Yearly** | ⭐999/год | Всё из Pro + экономия 44% |
| **Pro Lifetime** | ⭐2999 навсегда | Всё из Pro + пожизненный доступ + ранний доступ к фичам |

### Как купить / How to Buy

1. Откройте бота [@allstarspay_bot](https://t.me/allstarspay_bot) в Telegram
2. Выберите продукт **DevBadge Pro**
3. Оплатите подходящий план
4. Получите лицензионный ключ формата `SP-DVB-xxxx-xxxx`
5. Активируйте ключ:

```bash
devbadge pro activate SP-DVB-xxxx-xxxx
```

Или через переменную окружения:

```bash
export LICENSE_KEY=SP-DVB-xxxx-xxxx
devbadge generate --user octocat --all
```

### Конфигурация бота / Bot Config

```json
"devbadge": {
    "name": "DevBadge Pro",
    "description": "Динамические SVG-бейджи для GitHub — анимации, темы, без водяного знака",
    "plans": {
        "month": {"price": 149, "label": "1 месяц", "days": 30},
        "year": {"price": 999, "label": "1 год", "days": 365},
        "lifetime": {"price": 2999, "label": "Навсегда", "days": 0}
    },
    "prefix": "DVB"
}
```

---

## 🔑 License Verification

DevBadge Pro uses a multi-layer license verification system:

1. **Local Cache** — Cached verification result in `~/.devbadge/license_cache.json` (offline capable, 7-day TTL)
2. **Public Registry** — Checks `licenses.json` from [StarsPay Bot repo](https://github.com/sochiautoparts/stars-pay-bot)
3. **REST API Fallback** — Verifies via StarsPay API with `STARSPAY_API_KEY`

### Key Format

```
SP-DVB-xxxx-xxxx
│  │   │    │
│  │   │    └── Unique suffix (4 chars)
│  │   └── Product code (DVB = DevBadge)
│  └── StarsPay prefix
└── Service identifier
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `LICENSE_KEY` or `DEVBADGE_LICENSE` | Pro license key |
| `GITHUB_TOKEN` | GitHub personal access token |
| `STARSPAY_API_KEY` | StarsPay API key (for REST fallback) |
| `DEVBADGE_THEME` | Default theme |
| `DEVBADGE_OUTPUT` | Default output directory |

---

## 🤝 Contributing

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

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**[⭐ Get DevBadge Pro](https://t.me/allstarspay_bot)** · **[📚 Documentation](https://sochiautoparts.github.io/devbadge/)** · **[🐛 Report Bug](https://github.com/sochiautoparts/devbadge/issues)**

Made with ❤️ by [sochiautoparts](https://github.com/sochiautoparts)

</div>
