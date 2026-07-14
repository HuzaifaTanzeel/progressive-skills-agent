"""Lint skills/*/SKILL.md YAML frontmatter (required fields + L1 description budget)."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from harness.token_helpers import count_tokens

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SKILLS_DIR = REPO_ROOT / "skills"

MAX_DESCRIPTION_TOKENS = 50
ALLOWED_TIERS = frozenset({"read-only", "draft-only", "action-allowed"})
REQUIRED_FIELDS = ("name", "description")

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _parse_frontmatter(text: str) -> dict[str, object] | None:
    """Parse SKILL.md YAML frontmatter into a dict, or None if missing/invalid."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None
    raw = match.group(1)
    try:
        import yaml

        data = yaml.safe_load(raw)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _description_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return " ".join(str(value).split())


def check_skill_md(skill_md: Path, *, skills_dir: Path) -> list[str]:
    """Return error strings for one SKILL.md (empty = clean)."""
    errors: list[str] = []
    rel = skill_md.relative_to(skills_dir.parent) if skills_dir.parent in skill_md.parents else skill_md
    skill_dir_name = skill_md.parent.name

    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{rel}: cannot read file ({exc})"]

    fm = _parse_frontmatter(text)
    if fm is None:
        return [f"{rel}: missing or invalid YAML frontmatter (expected --- ... ---)"]

    for field in REQUIRED_FIELDS:
        if field not in fm or fm[field] is None or (
            isinstance(fm[field], str) and not fm[field].strip()
        ):
            errors.append(f"{rel}: missing required frontmatter field '{field}'")

    name = fm.get("name")
    if isinstance(name, str) and name.strip():
        if name.strip() != skill_dir_name:
            errors.append(
                f"{rel}: name '{name.strip()}' must match directory '{skill_dir_name}'"
            )

    desc = _description_text(fm.get("description"))
    if desc:
        tokens = count_tokens(desc)
        if tokens > MAX_DESCRIPTION_TOKENS:
            errors.append(
                f"{rel}: description is {tokens} tokens "
                f"(max {MAX_DESCRIPTION_TOKENS} for L1 catalog; "
                "keep trigger + anti-trigger short)"
            )

    tier = fm.get("tier")
    if tier is not None and str(tier).strip():
        tier_s = str(tier).strip()
        if tier_s not in ALLOWED_TIERS:
            errors.append(
                f"{rel}: tier '{tier_s}' must be one of "
                f"{', '.join(sorted(ALLOWED_TIERS))}"
            )

    return errors


def check_skills(skills_dir: Path | None = None) -> list[str]:
    """Return human-readable error strings; empty list = clean."""
    root = skills_dir or DEFAULT_SKILLS_DIR
    if not root.is_dir():
        return [f"skills directory not found: {root}"]

    errors: list[str] = []
    skill_dirs = sorted(d for d in root.iterdir() if d.is_dir() and not d.name.startswith("."))
    if not skill_dirs:
        return [f"no skill directories under {root}"]

    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"skills/{skill_dir.name}/SKILL.md: file missing")
            continue
        errors.extend(check_skill_md(skill_md, skills_dir=root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint skills/*/SKILL.md frontmatter (required fields + description budget)"
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=DEFAULT_SKILLS_DIR,
        help="Path to skills/ directory",
    )
    args = parser.parse_args()

    errors = check_skills(args.skills_dir)
    if not errors:
        print(f"OK: all skills under {args.skills_dir} pass frontmatter lint")
        return 0

    print(f"FAIL: {len(errors)} skill frontmatter issue(s):")
    for err in errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
