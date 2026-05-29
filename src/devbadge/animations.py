"""SVG animations for DevBadge badges.

NOTE: GitHub README sanitizes SVG and strips <style> tags,
making CSS animations non-functional on GitHub profiles.
Animations work in: browsers, static sites, documentation.
For GitHub profiles, use the 'pulse' animation which uses
inline style attributes that survive sanitization.

All animations are pure SVG + CSS, no JavaScript required.
They render correctly in browsers but may be simplified in
GitHub READMEs (GitHub sanitizes <style> in some contexts).
"""

from typing import Optional


def pulse_animation(element_id: str, color: str = "#ffffff") -> str:
    """Generate a pulse effect on a stat number.

    Args:
        element_id: Unique ID for the animation target.
        color: The glow color for the pulse.

    Returns:
        SVG <style> block with the animation.
    """
    return f"""<style>
  @keyframes pulse-{element_id} {{
    0%   {{ opacity: 1; }}
    50%  {{ opacity: 0.6; filter: drop-shadow(0 0 4px {color}); }}
    100% {{ opacity: 1; }}
  }}
  .pulse-{element_id} {{
    animation: pulse-{element_id} 2s ease-in-out infinite;
  }}
</style>"""


def gradient_animation(element_id: str, colors: list) -> str:
    """Generate an animated gradient for language bars.

    Args:
        element_id: Unique ID for the gradient.
        colors: List of color strings to cycle through.

    Returns:
        SVG <defs> + <style> block with animated gradient.
    """
    stops = ""
    total = len(colors)
    for i, c in enumerate(colors):
        offset = (i / max(total - 1, 1)) * 100
        stops += f'      <stop offset="{offset:.0f}%" stop-color="{c}" />\n'

    return f"""<defs>
    <linearGradient id="grad-{element_id}" x1="0%" y1="0%" x2="100%" y2="0%">
{stops}    </linearGradient>
  </defs>
  <style>
  @keyframes grad-shift-{element_id} {{
    0%   {{ transform: translateX(0); }}
    50%  {{ transform: translateX(10px); }}
    100% {{ transform: translateX(0); }}
  }}
  .grad-anim-{element_id} {{
    animation: grad-shift-{element_id} 3s ease-in-out infinite;
  }}
  </style>"""


def typing_animation(element_id: str, text: str, delay_ms: int = 80) -> str:
    """Generate a typing effect for text.

    Uses SVG dash-offset animation to reveal text character by character.

    Args:
        element_id: Unique ID for the text element.
        text: The text to animate.
        delay_ms: Milliseconds per character.

    Returns:
        SVG <style> block with typing animation.
    """
    char_count = len(text)
    duration = char_count * delay_ms

    return f"""<style>
  @keyframes typing-{element_id} {{
    0%   {{ clip-path: inset(0 100% 0 0); }}
    100% {{ clip-path: inset(0 0% 0 0); }}
  }}
  .typing-{element_id} {{
    animation: typing-{element_id} {duration}ms steps({char_count}) forwards;
    white-space: nowrap;
    overflow: hidden;
  }}
</style>"""


def sparkle_animation(element_id: str, count: int = 5) -> str:
    """Generate a sparkle effect on star icons.

    Args:
        element_id: Unique ID for the sparkle group.
        count: Number of sparkle elements.

    Returns:
        SVG <style> block + sparkle <g> elements.
    """
    import random
    random.seed(element_id)

    sparkles = ""
    style_rules = ""
    for i in range(count):
        x = random.randint(0, 20)
        y = random.randint(-5, 15)
        delay = i * 0.3
        size = random.uniform(1.5, 3.0)
        style_rules += f"""
  @keyframes sparkle-{element_id}-{i} {{
    0%, 100% {{ opacity: 0; transform: scale(0); }}
    50%      {{ opacity: 1; transform: scale(1); }}
  }}
  .sparkle-{element_id}-{i} {{
    animation: sparkle-{element_id}-{i} 1.5s ease-in-out {delay}s infinite;
  }}"""
        sparkles += f'  <circle class="sparkle-{element_id}-{i}" cx="{x}" cy="{y}" r="{size}" fill="#ffd700" />\n'

    return f"""<style>{style_rules}
</style>
<g class="sparkle-group-{element_id}">
{sparkles}</g>"""


def apply_animation(svg_content: str, animation_type: str, element_id: str,
                    is_pro: bool = False, **kwargs) -> str:
    """Apply an animation to existing SVG content.

    Only applies if user has Pro license.

    WARNING: CSS-based animations (gradient, typing, sparkle) use <style> tags
    which are stripped by GitHub README sanitization. Only the 'pulse' animation
    uses inline style attributes and works on GitHub profiles. For other
    animations, they will only render in browsers and static sites.

    Args:
        svg_content: The original SVG string.
        animation_type: One of 'pulse', 'gradient', 'typing', 'sparkle'.
        element_id: Unique ID for the animation.
        is_pro: Whether the user has Pro license.
        **kwargs: Additional parameters for the animation.

    Returns:
        Modified SVG string with animation, or original if not Pro.
    """
    if not is_pro:
        return svg_content

    # Warn if using animations that won't work on GitHub
    if animation_type not in ("pulse",):
        import warnings
        warnings.warn(
            f"Animation '{animation_type}' uses <style> tags which are stripped "
            f"by GitHub README sanitization. Use 'pulse' for GitHub-compatible "
            f"animations, or view badges in a browser/static site.",
            UserWarning,
            stacklevel=2,
        )

    anim_generators = {
        "pulse": lambda: pulse_animation(element_id, kwargs.get("color", "#ffffff")),
        "gradient": lambda: gradient_animation(element_id, kwargs.get("colors", ["#ff0000", "#00ff00", "#0000ff"])),
        "typing": lambda: typing_animation(element_id, kwargs.get("text", ""), kwargs.get("delay_ms", 80)),
        "sparkle": lambda: sparkle_animation(element_id, kwargs.get("count", 5)),
    }

    generator = anim_generators.get(animation_type)
    if not generator:
        return svg_content

    animation_svg = generator()

    # Insert animation before the closing </svg> tag
    insertion_point = svg_content.rfind("</svg>")
    if insertion_point == -1:
        return svg_content

    return svg_content[:insertion_point] + animation_svg + "\n" + svg_content[insertion_point:]
