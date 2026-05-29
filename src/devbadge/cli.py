"""CLI entry point for DevBadge."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from devbadge import __version__
from devbadge.badges import generate_badge
from devbadge.config import (
    DevBadgeConfig,
    init_config,
    is_pro,
    FREE_BADGES,
    PRO_BADGES,
    BADGE_TYPES,
)
from devbadge.themes import list_themes, list_free_themes


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="devbadge",
        description="DevBadge — Dynamic SVG badges for GitHub profiles",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate command
    gen = subparsers.add_parser("generate", help="Generate SVG badges")
    gen.add_argument("--user", "-u", required=True, help="GitHub username")
    gen.add_argument("--badge", "-b", dest="badges", default="commits,languages,stats,activity",
                     help=f"Comma-separated badge types: {', '.join(BADGE_TYPES)}")
    gen.add_argument("--all", action="store_true", help="Generate all available badges")
    gen.add_argument("--theme", "-t", default="default", help="Color theme name")
    gen.add_argument("--output", "-o", default="./badges", help="Output directory for SVG files")
    gen.add_argument("--token", help="GitHub personal access token")
    gen.add_argument("--license", dest="license_key", help="DevBadge Pro license key (SP-DVB-xxxx-xxxx)")
    gen.add_argument("--no-fetch", action="store_true", help="Skip API fetch, use cached/placeholder data")

    # init command
    subparsers.add_parser("init", help="Create a config file at ~/.devbadge/config.json")

    # pro command
    pro = subparsers.add_parser("pro", help="Pro license management")
    pro_sub = pro.add_subparsers(dest="pro_command", help="Pro subcommands")
    activate = pro_sub.add_parser("activate", help="Activate Pro license")
    activate.add_argument("key", help="License key (SP-DVB-xxxx-xxxx)")
    pro_sub.add_parser("status", help="Check license status")

    # themes command
    subparsers.add_parser("themes", help="List available themes")

    return parser


def cmd_generate(args: argparse.Namespace) -> int:
    """Execute the generate command."""
    from devbadge.config import is_pro as check_pro
    from devbadge.themes import get_theme

    # Determine license status
    license_key = args.license_key
    pro_user = check_pro(license_key)

    if pro_user:
        print("✨ Pro license activated!")
    else:
        print("ℹ️  Using free tier (some badges may have watermarks)")

    # Determine which badges to generate
    if args.all:
        badge_list = FREE_BADGES.copy()
        if pro_user:
            badge_list.extend(PRO_BADGES)
    else:
        badge_list = [b.strip() for b in args.badges.split(",")]

    # Validate theme
    theme = get_theme(args.theme)
    if theme.pro_only and not pro_user:
        print(f"⚠️  Theme '{args.theme}' is Pro-only. Falling back to 'default'.")
        theme = get_theme("default")

    # Fetch stats
    stats = None
    if not args.no_fetch:
        try:
            from devbadge.github_stats import fetch_stats
            print(f"📡 Fetching GitHub stats for @{args.user}...")
            stats = fetch_stats(args.user, token=args.token)
            print(f"   ✓ {stats.total_commits} commits, {stats.public_repos} repos, {stats.total_stars} stars")
        except Exception as e:
            print(f"⚠️  Failed to fetch stats: {e}")
            print("   Generating badges with placeholder data...")
            stats = None

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate each badge
    generated = 0
    for badge_type in badge_list:
        if badge_type not in BADGE_TYPES:
            print(f"⚠️  Unknown badge type: {badge_type}")
            continue

        try:
            svg = generate_badge(
                badge_type=badge_type,
                stats=stats,
                theme=args.theme if not (theme.pro_only and not pro_user) else "default",
                is_pro_user=pro_user,
                username=args.user,
            )
            output_file = output_dir / f"{badge_type}.svg"
            output_file.write_text(svg, encoding="utf-8")
            print(f"   ✓ Generated {badge_type} → {output_file}")
            generated += 1
        except Exception as e:
            print(f"   ✗ Failed to generate {badge_type}: {e}")

    print(f"\n🎉 Generated {generated}/{len(badge_list)} badges in {output_dir}/")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Execute the init command."""
    path = init_config()
    print(f"✅ Config file created at {path}")
    print("   Edit it to customize your DevBadge settings.")
    return 0


def cmd_pro(args: argparse.Namespace) -> int:
    """Execute the pro command."""
    if args.pro_command == "activate":
        from devbadge.config import _validate_key_format, _cache_license
        key = args.key
        if not _validate_key_format(key):
            print("❌ Invalid license key format. Expected: SP-DVB-xxxx-xxxx")
            return 1

        if is_pro(key):
            _cache_license(key, valid=True)
            # Save to config
            config = DevBadgeConfig.load()
            config.license_key = key
            config.save()
            print("✅ Pro license activated! All features unlocked.")
            return 0
        else:
            print("❌ License key is not valid or has expired.")
            print("   Purchase at https://t.me/allstarspay_bot")
            return 1

    elif args.pro_command == "status":
        config = DevBadgeConfig.load()
        key = config.license_key
        if not key:
            print("ℹ️  No license key configured.")
            print("   Use 'devbadge pro activate KEY' to activate.")
            print("   Purchase at https://t.me/allstarspay_bot")
            return 0

        if is_pro(key):
            print("✅ Pro license is active!")
            print(f"   Key: {key[:10]}****")
            return 0
        else:
            print("❌ Pro license is invalid or expired.")
            print("   Purchase at https://t.me/allstarspay_bot")
            return 1
    else:
        print("Unknown pro subcommand. Use 'activate' or 'status'.")
        return 1


def cmd_themes(args: argparse.Namespace) -> int:
    """List available themes."""
    print("\n🎨 Available Themes:\n")
    free = list_free_themes()
    all_themes = list_themes()

    print("  Free themes:")
    for name, theme in free.items():
        print(f"    • {name:15s}  bg={theme.background}  fg={theme.foreground}")

    print("\n  Pro themes (⭐):")
    for name, theme in all_themes.items():
        if theme.pro_only:
            animated = " (animated)" if theme.animated else ""
            print(f"    • {name:15s}  bg={theme.background}  fg={theme.foreground}{animated}")

    print()
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        return cmd_generate(args)
    elif args.command == "init":
        return cmd_init(args)
    elif args.command == "pro":
        return cmd_pro(args)
    elif args.command == "themes":
        return cmd_themes(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
