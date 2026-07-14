"""Token counting helpers for progressive-disclosure vs monolithic prompt comparison."""

from __future__ import annotations

from pathlib import Path

import tiktoken
from google.adk.skills.prompt import format_skills_as_xml
from google.adk.tools.skill_toolset import SkillToolset

DEFAULT_ENCODING = "cl100k_base"


def get_encoding(name: str = DEFAULT_ENCODING) -> tiktoken.Encoding:
    return tiktoken.get_encoding(name)


def count_tokens(text: str, encoding: tiktoken.Encoding | None = None) -> int:
    enc = encoding or get_encoding()
    return len(enc.encode(text))


def skill_md_body(skill_md_path: Path) -> str:
    """Return L2 body text (content below YAML frontmatter)."""
    text = skill_md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    return parts[2].lstrip("\n")


def load_all_reference_text(skill_dir: Path) -> str:
    refs_dir = skill_dir / "references"
    if not refs_dir.is_dir():
        return ""
    chunks: list[str] = []
    for ref_path in sorted(refs_dir.rglob("*")):
        if ref_path.is_file():
            chunks.append(ref_path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def l1_index_xml(toolset: SkillToolset) -> str:
    """L1 metadata XML returned by list_skills (name + description only)."""
    return format_skills_as_xml(toolset._list_skills())


def skill_system_instruction_text() -> str:
    """Compact skill protocol used by ProgressiveSkillToolset (not ADK default)."""
    from adk_app.progressive_skill_toolset import _COMPACT_SKILL_INSTRUCTION

    return _COMPACT_SKILL_INSTRUCTION
