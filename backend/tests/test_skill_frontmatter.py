"""Skill SKILL.md frontmatter lint (delegates to harness.lint_skills)."""

from harness.lint_skills import check_skills


def test_skill_frontmatter_clean() -> None:
    errors = check_skills()
    assert errors == [], "\n".join(errors)
