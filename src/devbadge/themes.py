"""Theme definitions for DevBadge."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Theme:
    """A color theme for badge rendering."""

    name: str
    background: str
    foreground: str
    accent: str
    secondary: str
    muted: str
    border: str
    title_color: str = ""
    text_color: str = ""
    bar_bg: str = ""
    pro_only: bool = False
    animated: bool = False

    def __post_init__(self):
        if not self.title_color:
            self.title_color = self.foreground
        if not self.text_color:
            self.text_color = self.foreground
        if not self.bar_bg:
            self.bar_bg = self.muted


THEMES: Dict[str, Theme] = {
    "default": Theme(
        name="default",
        background="#0d1b2a",
        foreground="#e0e1dd",
        accent="#415a77",
        secondary="#1b263b",
        muted="#778da9",
        border="#415a77",
    ),
    "dracula": Theme(
        name="dracula",
        background="#282a36",
        foreground="#f8f8f2",
        accent="#bd93f9",
        secondary="#44475a",
        muted="#6272a4",
        border="#bd93f9",
    ),
    "github-dark": Theme(
        name="github-dark",
        background="#0d1117",
        foreground="#c9d1d9",
        accent="#58a6ff",
        secondary="#161b22",
        muted="#8b949e",
        border="#30363d",
    ),
    "solarized": Theme(
        name="solarized",
        background="#002b36",
        foreground="#839496",
        accent="#268bd2",
        secondary="#073642",
        muted="#586e75",
        border="#094959",
    ),
    "nord": Theme(
        name="nord",
        background="#2e3440",
        foreground="#d8dee9",
        accent="#88c0d0",
        secondary="#3b4252",
        muted="#4c566a",
        border="#434c5e",
    ),
    "monokai": Theme(
        name="monokai",
        background="#272822",
        foreground="#f8f8f2",
        accent="#a6e22e",
        secondary="#3e3d32",
        muted="#75715e",
        border="#49483e",
    ),
    "neon": Theme(
        name="neon",
        background="#0a0a0a",
        foreground="#00ff88",
        accent="#ff00ff",
        secondary="#1a1a2e",
        muted="#555555",
        border="#00ff88",
        pro_only=True,
        animated=True,
    ),
    "aurora": Theme(
        name="aurora",
        background="#0f0c29",
        foreground="#e0e7ff",
        accent="#6366f1",
        secondary="#1a1a3e",
        muted="#818cf8",
        border="#4f46e5",
        pro_only=True,
        animated=True,
    ),
}

# Standard language colors (from GitHub linguist)
LANGUAGE_COLORS: Dict[str, str] = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Dart": "#00B4AB",
    "Scala": "#c22d40",
    "Shell": "#89e051",
    "Lua": "#000080",
    "R": "#198CE7",
    "Perl": "#0298c3",
    "Elixir": "#6e4a7e",
    "Haskell": "#5e5086",
    "Clojure": "#db5855",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
    "Jupyter Notebook": "#DA5B0B",
    "Dockerfile": "#384d54",
    "Makefile": "#427819",
}


def get_theme(name: str) -> Theme:
    """Get a theme by name, falling back to default."""
    return THEMES.get(name, THEMES["default"])


def list_themes() -> Dict[str, Theme]:
    """Return all available themes."""
    return THEMES.copy()


def list_free_themes() -> Dict[str, Theme]:
    """Return only free (non-Pro) themes."""
    return {k: v for k, v in THEMES.items() if not v.pro_only}
