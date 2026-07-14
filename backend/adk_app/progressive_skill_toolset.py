"""SkillToolset extensions for progressive disclosure + context hygiene.

Agent Skills whitepaper (Day 3):
- L1 (name + description) stays **always** in the system prompt — pay a small
  fixed metadata tax every turn; do **not** discover names via list_skills.
- L2 body loads only on load_skill; L3 resources/scripts on demand.
- Capability Profile teardown: only one skill's domain tools stay active.

Stock ADK SkillToolset keeps ListSkillsTool, which *disables* L1 injection and
forces an extra tool round-trip. Models then guess kebab-case names, fail, and
pollute history with list_skills XML — the failure mode in production traces.
"""

from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from google.adk.skills import prompt
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.skill_toolset import ListSkillsTool
from google.adk.tools.skill_toolset import LoadSkillTool
from google.adk.tools.skill_toolset import SkillToolset
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from typing_extensions import override

if TYPE_CHECKING:
  from google.adk.models.llm_request import LlmRequest

# Compact replacement for ADK's long DEFAULT_SKILL_SYSTEM_INSTRUCTION (~445 toks).
_COMPACT_SKILL_INSTRUCTION = (
    "Skills extend you with on-demand runbooks. Exact skill <name> values are "
    "listed in <available_skills> below — pass those strings to load_skill; "
    "never invent or paraphrase names.\n"
    "1. Match the user request to one skill description, then call "
    "load_skill(skill_name=<exact name>).\n"
    "2. Follow that skill's instructions in the same turn (call its domain "
    "tools, then answer). Loading a skill does not finish the turn.\n"
    "3. load_skill_resource is only for files under that skill's "
    "references/, assets/, or scripts/. run_skill_script runs scripts/.\n"
    "4. Only one skill stays active: loading another unloads the previous. "
    "Call unload_skill when the topic changes or a workflow is finished.\n"
    "5. On load_skill / resource / script errors, report them; do not invent "
    "a substitute answer from general knowledge."
)


def activated_skills_state_key(agent_name: str) -> str:
    return f"_adk_activated_skill_{agent_name}"


class UnloadSkillTool(BaseTool):
    """Deactivate a skill so its domain tools leave the tool list."""

    def __init__(self, toolset: "ProgressiveSkillToolset"):
        super().__init__(
            name="unload_skill",
            description=(
                "Deactivates loaded skill(s) and removes their domain tools. "
                "Pass skill_name, or omit/'*' for all. Use when switching topics."
            ),
        )
        self._toolset = toolset

    def _get_declaration(self) -> types.FunctionDeclaration | None:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": (
                            "Exact skill name to unload, or '*' for all. "
                            "Optional; omit to unload all."
                        ),
                    },
                },
            },
        )

    async def run_async(
        self, *, args: dict[str, Any], tool_context: ToolContext
    ) -> Any:
        state_key = activated_skills_state_key(tool_context.agent_name)
        current = list(tool_context.state.get(state_key) or [])
        skill_name = args.get("skill_name")

        if not skill_name or skill_name == "*":
            tool_context.state[state_key] = []
            return {
                "unloaded": current,
                "activated_skills": [],
                "message": "All skills deactivated.",
            }

        if skill_name not in current:
            return {
                "unloaded": [],
                "activated_skills": current,
                "message": f"Skill '{skill_name}' was not activated.",
            }

        remaining = [s for s in current if s != skill_name]
        tool_context.state[state_key] = remaining
        return {
            "unloaded": [skill_name],
            "activated_skills": remaining,
            "message": f"Skill '{skill_name}' deactivated.",
        }


class SingleActiveLoadSkillTool(LoadSkillTool):
    """load_skill that keeps only one Capability Profile active at a time."""

    @override
    async def run_async(
        self, *, args: dict[str, Any], tool_context: ToolContext
    ) -> Any:
        state_key = activated_skills_state_key(tool_context.agent_name)
        previous = list(tool_context.state.get(state_key) or [])

        result = await super().run_async(args=args, tool_context=tool_context)
        if not isinstance(result, dict) or result.get("error"):
            return result

        skill_name = result.get("skill_name") or args.get("skill_name")
        if not skill_name:
            return result

        replaced = [s for s in previous if s != skill_name]
        tool_context.state[state_key] = [skill_name]
        result["activated_skills"] = [skill_name]
        if replaced:
            result["unloaded_previous_skills"] = replaced
            result["context_note"] = (
                "Previous skills unloaded (single Capability Profile). "
                "Follow only this skill's instructions."
            )
        return result


class ProgressiveSkillToolset(SkillToolset):
    """L1-always-on catalog + single-active load + unload_skill."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # Drop ListSkillsTool so ADK (and our override) inject L1 every turn
        # instead of forcing a discovery tool call.
        self._tools = [
            t
            for t in self._tools
            if not isinstance(t, (LoadSkillTool, ListSkillsTool))
        ]
        self._tools.insert(0, SingleActiveLoadSkillTool(self))
        insert_at = len(self._tools)
        for i, t in enumerate(self._tools):
            if t.name == "run_skill_script":
                insert_at = i + 1
                break
        self._tools.insert(insert_at, UnloadSkillTool(self))

    @override
    async def process_llm_request(
        self, *, tool_context: ToolContext, llm_request: LlmRequest
    ) -> None:
        """Inject compact skill protocol + always-on L1 metadata (paper §2/§5)."""
        skills_xml = prompt.format_skills_as_xml(self._list_skills())
        llm_request.append_instructions(
            [_COMPACT_SKILL_INSTRUCTION, skills_xml]
        )
