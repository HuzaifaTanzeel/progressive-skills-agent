from .agent_factory import REPO_SKILLS_DIR, build_app, build_root_agent

root_agent = build_root_agent(REPO_SKILLS_DIR)
app = build_app(REPO_SKILLS_DIR)
