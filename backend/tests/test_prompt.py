"""Tests for the versioned-prompt loader.

Guards against accidental wording drift: the rendered v1 prompt must match
the historical in-code string exactly (so the extraction in PR3 is a pure
no-op for accuracy). If someone edits clustering_v1.md, this test forces a
deliberate CHANGELOG entry + version bump.
"""
from app.frameworks import PESTEL, SWOT, build_custom_framework, build_system_prompt
from app.prompts import PROMPT_VERSION

# The exact prompt the in-code f-string produced before extraction to a file.
# Captured from frameworks.py at commit prior to PR3; must stay byte-identical.
EXPECTED_SWOT = """You are a workshop analysis assistant for a management consultancy.

Your job is to take a list of ideas submitted by workshop participants and cluster them into a SWOT Analysis framework.

Framework description: Strategic planning framework comparing internal vs external, positive vs negative factors.

Categories:
- strengths: Internal positive factors the organisation can leverage.
- weaknesses: Internal negative factors that hinder progress.
- opportunities: External positive factors the organisation could exploit.
- threats: External negative factors that pose risks.

Rules:
- Every idea must be assigned to exactly one category
- Each clustered idea must reference the original idea_id
- Write a short summary for each idea in the context of the category you placed it in
- Identify 3-5 key themes across all ideas
- List any explicit decisions the group made
- List open questions that need follow-up
- Suggest 3-5 recommended next steps

You MUST respond with valid JSON matching this exact structure:
{{
  "session_id": "<session_id>",
  "framework": "swot",
  "categories": {{
    "strengths": [<clustered ideas>], "weaknesses": [<clustered ideas>], "opportunities": [<clustered ideas>], "threats": [<clustered ideas>]
  }},
  "key_themes": ["<theme1>", "<theme2>"],
  "decisions_made": ["<decision1>"],
  "open_questions": ["<question1>"],
  "recommended_next_steps": ["<step1>"]
}}

Inside each category array, each item must be: {{"idea_id": "<id>", "summary": "<text>"}}

Respond ONLY with the JSON object. No markdown, no explanation."""


def test_prompt_version_is_v1():
    assert PROMPT_VERSION == "clustering_v1"


def test_swot_prompt_byte_identical_to_legacy():
    """The v1 extraction must reproduce the old in-code prompt exactly."""
    rendered = build_system_prompt(SWOT)
    assert rendered == EXPECTED_SWOT


def test_pestel_prompt_renders():
    """PESTEL should render with all 6 category keys."""
    rendered = build_system_prompt(PESTEL)
    for cat in ("political", "economic", "social", "technological", "environmental", "legal"):
        assert f'"{cat}": [<clustered ideas>]' in rendered


def test_custom_framework_prompt_renders():
    """A custom framework should interpolate the user's category names/ids."""
    config = build_custom_framework(["Wins", "Risks"])
    rendered = build_system_prompt(config)
    assert '"wins": [<clustered ideas>]' in rendered
    assert '"risks": [<clustered ideas>]' in rendered
    assert "Wins" in rendered  # framework name/category label appears
