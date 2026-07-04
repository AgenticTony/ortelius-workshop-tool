"""Prompt template loading + versioning.

Prompts live as files in backend/prompts/ (config, not code) so a wording
change doesn't require a redeploy of Python. This module loads + renders
them at runtime and exposes the current PROMPT_VERSION for logging.
"""
from __future__ import annotations

import functools
from pathlib import Path

# The current prompt version. Bump when introducing a new clustering_vN.md and
# record the change in prompts/CHANGELOG.md. Logged on every Claude call.
PROMPT_VERSION = "clustering_v2"

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@functools.lru_cache(maxsize=8)
def _load_raw(version: str) -> str:
    """Load the raw template text for a version (cached).

    Strips a single trailing newline so the rendered prompt matches the
    historical in-code f-string (which had none) — see test_prompt.py.
    """
    path = _PROMPTS_DIR / f"{version}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt template {path} not found. Known versions live in {_PROMPTS_DIR}."
        )
    text = path.read_text(encoding="utf-8")
    if text.endswith("\n"):
        text = text[:-1]
    return text


def render_clustering_prompt(
    *,
    framework_name: str,
    framework_id: str,
    framework_description: str,
    categories_block: str,
    categories_json_keys: str,
    session_id: str,
    version: str = PROMPT_VERSION,
) -> str:
    """Render the clustering system prompt for a framework config.

    The template uses ``{name}`` placeholders that are NOT Python format
    fields, so we do targeted str.replace rather than str.format. The JSON
    example's literal braces are single ``{``/``}`` in the template (v1 wrongly
    doubled them — a leftover from a .format() era that produced invalid JSON
    in the example). ``session_id`` is injected so the model echoes the real id
    rather than a ``<session_id>`` placeholder (AnalysisResult requires it).
    """
    template = _load_raw(version)
    return (
        template
        .replace("{framework_name}", framework_name)
        .replace("{framework_id}", framework_id)
        .replace("{framework_description}", framework_description)
        .replace("{categories_block}", categories_block)
        .replace("{categories_json_keys}", categories_json_keys)
        .replace("{session_id}", session_id)
    )
