"""SVG animations for DevBadge badges using SMIL only.

All animations use SMIL (<animate>, <animateTransform>) which GitHub
DOES support in README SVGs. No <style> tags or CSS animations are used.

SMIL animations that work on GitHub:
- <animate> for attribute transitions (opacity, fill, etc.)
- <animateTransform> for transforms (scale, rotate, translate)
- <set> for discrete attribute changes

GitHub strips <style> tags from SVGs, so we never use CSS keyframes.
"""

from typing import Optional


def pulse_animation(element_id: str, color: str = "#ffffff") -> str:
    """Generate a pulse effect using SMIL <animate>.

    Pulses the opacity of a referenced element, creating a breathing glow effect.

    Args:
        element_id: Unique ID for the animation target.
        color: The glow color for the pulse.

    Returns:
        SVG elements with SMIL animation (no <style> tags).
    """
    # SMIL animate on opacity — works on GitHub
    return f"""<g id="pulse-{element_id}">
    <animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite" />
  </g>"""


def gradient_animation(element_id: str, colors: list) -> str:
    """Generate an animated gradient using SMIL <animate>.

    Cycles through colors by animating the stop-color of gradient stops.
    GitHub supports SMIL <animate> on SVG gradient stops.

    Args:
        element_id: Unique ID for the gradient.
        colors: List of color strings to cycle through.

    Returns:
        SVG <defs> with animated gradient stops (SMIL only).
    """
    if not colors or len(colors) < 2:
        colors = ["#ff0000", "#00ff00"]

    # Create gradient with animated stops
    # Each stop animates through the color list
    num_stops = min(len(colors), 4)
    stops = ""
    for i in range(num_stops):
        offset = (i / max(num_stops - 1, 1)) * 100
        initial_color = colors[i % len(colors)]
        # Cycle through all colors
        color_values = ";".join(colors[i % len(colors):] + colors[:i % len(colors)])
        stops += f"""      <stop offset="{offset:.0f}%">
        <animate attributeName="stop-color" values="{color_values}" dur="4s" repeatCount="indefinite" />
      </stop>
"""

    return f"""<defs>
    <linearGradient id="grad-{element_id}" x1="0%" y1="0%" x2="100%" y2="0%">
{stops}    </linearGradient>
  </defs>"""


def typing_animation(element_id: str, text: str, delay_ms: int = 80) -> str:
    """Generate a typing effect using SMIL <animate>.

    Reveals text from left to right using animated clip-path or
    width reveal. Uses <animate> on a mask/clip rect width.

    Args:
        element_id: Unique ID for the text element.
        text: The text to animate.
        delay_ms: Milliseconds per character.

    Returns:
        SVG elements with SMIL typing animation.
    """
    char_count = len(text) if text else 1
    duration = char_count * delay_ms
    text_width = char_count * 7  # Approximate width per character at font-size 11

    # Use SMIL to animate a clip rect from 0 to full width
    return f"""<defs>
    <clipPath id="typing-clip-{element_id}">
      <rect x="0" y="0" width="0" height="30">
        <animate attributeName="width" from="0" to="{text_width}" dur="{duration}ms" fill="freeze" begin="0.5s" />
      </rect>
    </clipPath>
  </defs>"""


def sparkle_animation(element_id: str, count: int = 5) -> str:
    """Generate a sparkle effect using SMIL <animate>.

    Creates small circles that appear and disappear with
    <animate> on opacity and <animateTransform> on scale.

    Args:
        element_id: Unique ID for the sparkle group.
        count: Number of sparkle elements.

    Returns:
        SVG sparkle elements with SMIL animation (no <style> tags).
    """
    import random
    random.seed(element_id)

    sparkles = ""
    for i in range(count):
        x = random.randint(0, 20)
        y = random.randint(-5, 15)
        delay = i * 0.3
        size = random.uniform(1.5, 3.0)
        # SMIL animate opacity: fade in/out
        # SMIL animateTransform: scale from 0 to 1
        sparkles += f"""  <circle cx="{x}" cy="{y}" r="{size}" fill="#ffd700" opacity="0">
    <animate attributeName="opacity" values="0;1;0" dur="1.5s" begin="{delay}s" repeatCount="indefinite" />
    <animateTransform attributeName="transform" type="scale" values="0;1;0" dur="1.5s" begin="{delay}s" repeatCount="indefinite" />
  </circle>
"""

    return f"""<g id="sparkle-group-{element_id}">
{sparkles}</g>"""


def apply_animation(svg_content: str, animation_type: str, element_id: str,
                    is_pro: bool = False, **kwargs) -> str:
    """Apply an animation to existing SVG content using SMIL only.

    All animations use SMIL (<animate>, <animateTransform>) which
    GitHub DOES support in README SVGs. No <style> tags are used.

    Args:
        svg_content: The original SVG string.
        animation_type: One of 'pulse', 'gradient', 'typing', 'sparkle'.
        element_id: Unique ID for the animation.
        is_pro: Whether the user has Pro license.
        **kwargs: Additional parameters for the animation.

    Returns:
        Modified SVG string with SMIL animation, or original if not Pro.
    """
    if not is_pro:
        return svg_content

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

    # For pulse, wrap content in an animated group
    if animation_type == "pulse":
        # Insert pulse animation group before closing </svg>
        insertion_point = svg_content.rfind("</svg>")
        if insertion_point == -1:
            return svg_content
        # Add the pulse group that affects subsequent elements
        return svg_content[:insertion_point] + animation_svg + "\n" + svg_content[insertion_point:]

    # For gradient, insert <defs> after the opening <svg> tag
    if animation_type == "gradient":
        # Find the first > after <svg
        svg_open_end = svg_content.find(">", svg_content.find("<svg"))
        if svg_open_end == -1:
            return svg_content
        insert_pos = svg_open_end + 1
        return svg_content[:insert_pos] + "\n" + animation_svg + svg_content[insert_pos:]

    # For typing, insert <defs> with clipPath
    if animation_type == "typing":
        svg_open_end = svg_content.find(">", svg_content.find("<svg"))
        if svg_open_end == -1:
            return svg_content
        insert_pos = svg_open_end + 1
        return svg_content[:insert_pos] + "\n" + animation_svg + svg_content[insert_pos:]

    # For sparkle, insert before closing </svg>
    insertion_point = svg_content.rfind("</svg>")
    if insertion_point == -1:
        return svg_content
    return svg_content[:insertion_point] + animation_svg + "\n" + svg_content[insertion_point:]
