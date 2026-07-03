import json
import logging
import time

import anthropic

from app.config import settings
from app.errors import (
    ClaudeAPIError,
    ClaudeParseError,
    FrameworkNotFoundError,
    InvalidFrameworkError,
)
from app.frameworks import (
    FrameworkConfig,
    get_framework,
    build_custom_framework,
    build_system_prompt,
)
from app.models import AnalysisResult
from app.prompts import PROMPT_VERSION

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(
    api_key=settings.claude_api_key,
    base_url=settings.claude_base_url,
)

CORRECTIVE_PROMPT = (
    "Your previous response was not valid JSON. "
    "Return ONLY the JSON object with no markdown formatting, "
    "no code fences, and no explanation."
)

# Claude model for idea clustering. Configurable so a model retirement (the
# previous hardcoded "claude-sonnet-4-20250514" 404'd) is an env change, not
# a code change. Sonnet 4.5 is a good quality/cost balance for this task.
CLAUDE_MODEL = settings.claude_model


def _resolve_config(
    framework: str,
    custom_categories: list[str] | None,
) -> FrameworkConfig:
    """Resolve framework string + optional categories into a FrameworkConfig.

    Raises FrameworkNotFoundError / InvalidFrameworkError — these were
    previously uncaught ValueErrors on the analysis path (opaque 500s).
    """
    try:
        if framework == "custom":
            return build_custom_framework(custom_categories or [])
        return get_framework(framework)
    except ValueError as e:
        msg = str(e)
        if "Unknown framework" in msg or framework != "custom":
            raise FrameworkNotFoundError(framework) from e
        raise InvalidFrameworkError(msg) from e


def _call_claude(
    system_prompt: str,
    user_message: str,
    *,
    framework_id: str,
) -> str:
    """Call Claude API and return raw text. Retries once on bad JSON.

    Logs every call (prompt version, framework, tokens, latency, retry) so
    cost and quality are observable. Raises ClaudeAPIError on any upstream
    Anthropic/network failure so the caller gets a clean 503.
    """
    started = time.monotonic()
    retry_attempted = False
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
    except anthropic.AnthropicError as e:
        logger.warning("Claude API call failed: %s", e)
        raise ClaudeAPIError() from e

    raw = response.content[0].text.strip()

    try:
        json.loads(raw)
        _log_call(framework_id, response, started, retry_attempted=False)
        return raw
    except json.JSONDecodeError:
        logger.warning("Claude returned invalid JSON, retrying with corrective prompt")
        retry_attempted = True

    try:
        retry = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": raw},
                {"role": "user", "content": CORRECTIVE_PROMPT},
            ],
        )
    except anthropic.AnthropicError as e:
        logger.warning("Claude API retry call failed: %s", e)
        raise ClaudeAPIError() from e
    _log_call(framework_id, retry, started, retry_attempted=True)
    return retry.content[0].text.strip()


def _log_call(
    framework_id: str,
    response: "anthropic.types.Message",
    started: float,
    *,
    retry_attempted: bool,
) -> None:
    """Structured log line per Claude call: version, framework, tokens, latency."""
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "input_tokens", None) if usage else None
    output_tokens = getattr(usage, "output_tokens", None) if usage else None
    latency_ms = int((time.monotonic() - started) * 1000)
    logger.info(
        "claude_call prompt_version=%s framework=%s model=%s "
        "input_tokens=%s output_tokens=%s latency_ms=%d retry=%s",
        PROMPT_VERSION,
        framework_id,
        CLAUDE_MODEL,
        input_tokens,
        output_tokens,
        latency_ms,
        retry_attempted,
    )


def analyse_ideas(
    session_id: str,
    framework: str,
    ideas: list[dict],
    custom_categories: list[str] | None = None,
    session_topic: str | None = None,
) -> AnalysisResult:
    """Send ideas to Claude for analysis using the resolved framework config.

    session_topic gives Claude real context (previously hardcoded to
    "(workshop)"); the analysis route has the session object and passes it.
    """
    config = _resolve_config(framework, custom_categories)
    system_prompt = build_system_prompt(config)

    idea_list = "\n".join(
        f"- ID: {idea['id']}, Participant: {idea.get('participant_name', 'Unknown')}, "
        f"Content: {idea['content']}"
        for idea in ideas
    )

    topic = session_topic or "(workshop)"
    user_message = (
        f"Session ID: {session_id}\n"
        f"Session topic: {topic}\n"
        f"Framework: {config.name}\n\n"
        f"Participant ideas:\n{idea_list}\n\n"
        f"Analyse these ideas and cluster them into "
        f"{config.name} categories."
    )

    raw = _call_claude(system_prompt, user_message, framework_id=config.id)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        # The retry inside _call_claude already failed to produce JSON.
        logger.warning("Claude response unparseable after retry: %s", raw[:200])
        raise ClaudeParseError() from e
    return AnalysisResult(**parsed)
