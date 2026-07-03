"""Pluggable framework registry for workshop analysis.

Defines what a framework looks like (Category, Axis, FrameworkConfig),
provides built-in configs (SWOT, PESTEL), and builds Claude prompts
dynamically from any registered framework.

Adding a new framework = adding a dict entry. No code changes elsewhere.
"""

from pydantic import BaseModel

class Category(BaseModel):
    """One box in the analysis framework matrix."""
    id: str
    name: str
    description: str


class Axis(BaseModel):
    """Optional metadata for matrix-form PDF rendering (deferred)."""
    label: str
    values: list[str]


class FrameworkConfig(BaseModel):
    """Complete definition of an analysis framework."""
    id: str
    name: str
    description: str
    categories: list[Category]
    axes: dict[str, Axis] | None = None


# ── Built-in frameworks ─────────────────────────────────────

SWOT = FrameworkConfig(
    id="swot",
    name="SWOT Analysis",
    description="Strategic planning framework comparing internal vs external, positive vs negative factors.",
    categories=[
        Category(
            id="strengths",
            name="Strengths",
            description="Internal positive factors the organisation can leverage.",
        ),
        Category(
            id="weaknesses",
            name="Weaknesses",
            description="Internal negative factors that hinder progress.",
        ),
        Category(
            id="opportunities",
            name="Opportunities",
            description="External positive factors the organisation could exploit.",
        ),
        Category(
            id="threats",
            name="Threats",
            description="External negative factors that pose risks.",
        ),
    ],
    axes={
        "source": Axis(label="Source", values=["Internal", "External"]),
        "valence": Axis(label="Valence", values=["Positive", "Negative"]),
    },
)

PESTEL = FrameworkConfig(
    id="pestel",
    name="PESTEL Analysis",
    description="Macro-environmental framework for understanding external forces affecting an organisation.",
    categories=[
        Category(
            id="political",
            name="Political",
            description=(
                "Government policies, regulations, "
                "political stability, trade policy."
            ),
        ),
        Category(
            id="economic",
            name="Economic",
            description=(
                "Growth rates, inflation, exchange rates, "
                "interest rates, unemployment."
            ),
        ),
        Category(
            id="social",
            name="Social",
            description=(
                "Demographics, cultural trends, education, "
                "lifestyle changes, health awareness."
            ),
        ),
        Category(
            id="technological",
            name="Technological",
            description=(
                "Innovation, automation, R&D, "
                "digital disruption, technology adoption."
            ),
        ),
        Category(
            id="environmental",
            name="Environmental",
            description=(
                "Climate change, sustainability, "
                "carbon footprint, ecological regulations."
            ),
        ),
        Category(
            id="legal",
            name="Legal",
            description=(
                "Employment law, consumer protection, "
                "health & safety, data protection."
            ),
        ),
    ],
)

_REGISTRY: dict[str, FrameworkConfig] = {
    "swot": SWOT,
    "pestel": PESTEL,
}


# ── Lookup ───────────────────────────────────────────────────

def get_framework(framework_id: str) -> FrameworkConfig:
    """Look up a built-in framework by ID.

    Raises ValueError if the ID is not in the registry.
    """
    if framework_id not in _REGISTRY:
        raise ValueError(
            f"Unknown framework '{framework_id}'. "
            f"Available: {', '.join(sorted(_REGISTRY.keys()))}"
        )
    return _REGISTRY[framework_id]


def build_custom_framework(categories: list[str]) -> FrameworkConfig:
    """Build a FrameworkConfig from user-supplied category names.

    Used when a facilitator creates a session with framework='custom'.
    Category IDs are derived from names (lowercased, spaces→underscores).
    """
    if len(categories) < 2:
        raise ValueError("Custom frameworks need at least 2 categories.")

    cats = []
    for name in categories:
        cat_id = name.strip().lower().replace(" ", "_")
        cats.append(Category(
            id=cat_id,
            name=name.strip(),
            description=f"Workshop ideas related to: {name.strip()}.",
        ))

    return FrameworkConfig(
        id="custom",
        name="Custom Framework",
        description="A user-defined analysis framework.",
        categories=cats,
    )


# ── Prompt builder ───────────────────────────────────────────

def build_system_prompt(config: FrameworkConfig) -> str:
    """Generate the Claude system prompt for a given framework config.

    Injects category names and descriptions so Claude knows exactly
    what each category means — not just its label.
    """
    cat_block = "\n".join(
        f"- {c.id}: {c.description}" for c in config.categories
    )

    cat_json_keys = ", ".join(f'"{c.id}": [<clustered ideas>]' for c in config.categories)

    return f"""You are a workshop analysis assistant for a management consultancy.

Your job is to take a list of ideas submitted by workshop participants and cluster them into a {config.name} framework.

Framework description: {config.description}

Categories:
{cat_block}

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
  "framework": "{config.id}",
  "categories": {{
    {cat_json_keys}
  }},
  "key_themes": ["<theme1>", "<theme2>"],
  "decisions_made": ["<decision1>"],
  "open_questions": ["<question1>"],
  "recommended_next_steps": ["<step1>"]
}}

Inside each category array, each item must be: {{"idea_id": "<id>", "summary": "<text>"}}

Respond ONLY with the JSON object. No markdown, no explanation."""
