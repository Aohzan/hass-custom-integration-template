"""Rename the integration created from the template.

Replaces the domain, the name, the class prefix and the repository of the
template in every tracked file, and moves the integration directory.

Usage:
    python scripts/rename.py my_domain "My Integration" Owner/repository
"""

import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "integration_blueprint"
NAME = "Integration Blueprint"
PACKAGE = "integration-blueprint"
CLASS_PREFIX = "Blueprint"
REPOSITORY = "Aohzan/hass-custom-integration-template"
# The release guard of the CI must keep the name of the template repository
KEEP_REPOSITORY = {Path(".github/workflows/ci.yaml"), Path("scripts/rename.py")}


def main() -> None:
    """Run the script."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("domain", help="domain of the integration, like my_domain")
    parser.add_argument("name", help='name of the integration, like "My Integration"')
    parser.add_argument("repository", help="GitHub repository, like Owner/repository")
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.domain):
        raise SystemExit("The domain must be lowercase letters, digits and underscores")
    class_prefix = "".join(word.capitalize() for word in args.domain.split("_"))
    replacements = [
        (DOMAIN, args.domain),
        (NAME, args.name),
        (PACKAGE, args.domain.replace("_", "-")),
        (CLASS_PREFIX, class_prefix),
    ]

    files = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    for name in files:
        path = ROOT / name
        if path.suffix not in {
            ".py",
            ".json",
            ".toml",
            ".yaml",
            ".yml",
            ".md",
            ".ambr",
        }:
            continue
        text = original = path.read_text(encoding="utf-8")
        if Path(name) not in KEEP_REPOSITORY:
            text = text.replace(REPOSITORY, args.repository)
        if Path(name) != Path("scripts/rename.py"):
            for old, new in replacements:
                text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")

    subprocess.run(
        [
            "git",
            "mv",
            f"custom_components/{DOMAIN}",
            f"custom_components/{args.domain}",
        ],
        cwd=ROOT,
        check=True,
    )
    print(f"Renamed to {args.domain}: run `uv lock` and review `git diff`")


if __name__ == "__main__":
    main()
