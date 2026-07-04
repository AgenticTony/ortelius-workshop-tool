"""Tests for the versioned-prompt loader.

The rendered prompt is asserted exactly so accidental wording drift forces a
deliberate CHANGELOG entry + version bump (see prompts/CHANGELOG.md).
"""
from app.frameworks import PESTEL, SWOT, build_custom_framework, build_system_prompt
from app.prompts import PROMPT_VERSION

# The exact SWOT prompt v2 produces. session_id is injected (AnalysisResult
# requires it — v1 left a "<session_id>" placeholder). The JSON example uses
# single braces (v1 wrongly doubled them, a .format()-era leftover that made
# the "exact structure" example invalid JSON).
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
{
  "session_id": "s1",
  "framework": "swot",
  "categories": {
    "strengths": [<clustered ideas>], "weaknesses": [<clustered ideas>], "opportunities": [<clustered ideas>], "threats": [<clustered ideas>]
  },
  "key_themes": ["<theme1>", "<theme2>"],
  "decisions_made": ["<decision1>"],
  "open_questions": ["<question1>"],
  "recommended_next_steps": ["<step1>"]
}

Inside each category array, each item must be: {"idea_id": "<id>", "summary": "<text>"}

Respond ONLY with the JSON object. No markdown, no explanation."""


def test_prompt_version_is_v2():
    assert PROMPT_VERSION == "clustering_v2"


def test_swot_prompt_renders_expected():
    """The v2 SWOT prompt: session_id injected, valid (single-brace) JSON skeleton."""
    rendered = build_system_prompt(SWOT, "s1")
    assert rendered == EXPECTED_SWOT


def test_swot_prompt_has_no_double_braces_and_substitutes_session_id():
    """Regression guard for the two v1 defects.

    v1 left literal ``{{``/``}}`` (invalid JSON in the example) and an
    unsubstituted ``<session_id>`` placeholder. Both must stay fixed.
    """
    rendered = build_system_prompt(SWOT, "s1")
    assert "{{" not in rendered
    assert "}}" not in rendered
    assert "<session_id>" not in rendered
    assert '"session_id": "s1"' in rendered


def test_pestel_prompt_renders():
    """PESTEL should render with all 6 category keys and the real session_id."""
    rendered = build_system_prompt(PESTEL, "pestel-session")
    for cat in ("political", "economic", "social", "technological", "environmental", "legal"):
        assert f'"{cat}": [<clustered ideas>]' in rendered
    assert '"session_id": "pestel-session"' in rendered


def test_custom_framework_prompt_renders():
    """A custom framework should interpolate the user's category names/ids."""
    config = build_custom_framework(["Wins", "Risks"])
    rendered = build_system_prompt(config, "custom-session")
    assert '"wins": [<clustered ideas>]' in rendered
    assert '"risks": [<clustered ideas>]' in rendered
    assert "Wins" in rendered  # framework name/category label appears
    assert '"session_id": "custom-session"' in rendered
