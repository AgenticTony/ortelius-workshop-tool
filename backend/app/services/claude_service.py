import json

import anthropic

from app.config import settings
from app.models import AnalysisResult

client = anthropic.Anthropic(
    api_key=settings.claude_api_key,
    base_url=settings.claude_base_url,
)

SWOT_SYSTEM_PROMPT = """You are a workshop analysis assistant for a management consultancy.

Your job is to take a list of ideas submitted by workshop participants and cluster them into a SWOT framework.

Rules:
- Every idea must be assigned to exactly one category: strengths, weaknesses, opportunities, or threats
- Each clustered idea must reference the original idea_id
- Write a short summary for each idea in the context of the category you placed it in
- Identify 3-5 key themes across all ideas
- List any explicit decisions the group made
- List open questions that need follow-up
- Suggest 3-5 recommended next steps

You MUST respond with valid JSON matching this exact structure:
{
  "session_id": "<session_id>",
  "framework": "swot",
  "categories": {
    "strengths": [{"idea_id": "<id>", "summary": "<text>"}],
    "weaknesses": [{"idea_id": "<id>", "summary": "<text>"}],
    "opportunities": [{"idea_id": "<id>", "summary": "<text>"}],
    "threats": [{"idea_id": "<id>", "summary": "<text>"}]
  },
  "key_themes": ["<theme1>", "<theme2>"],
  "decisions_made": ["<decision1>"],
  "open_questions": ["<question1>"],
  "recommended_next_steps": ["<step1>"]
}

Respond ONLY with the JSON object. No markdown, no explanation."""


def analyse_ideas(session_id: str, framework: str, ideas: list[dict]) -> AnalysisResult:
    """Send ideas to Claude for analysis and return structured result."""
    idea_list = "\n".join(
        f"- ID: {idea['id']}, Participant: {idea.get('participant_name', 'Unknown')}, "
        f"Content: {idea['content']}"
        for idea in ideas
    )

    user_message = f"""Session topic: (workshop)
Framework: {framework}

Participant ideas:
{idea_list}

Analyse these ideas and cluster them into {framework.upper()} categories."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SWOT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text
    parsed = json.loads(raw)
    return AnalysisResult(**parsed)
