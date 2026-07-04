# Frameworks — adding a new analysis framework

The Workshop Tool clusters participant ideas into an analysis framework. **SWOT, PESTEL, and custom frameworks all flow through the same code path.** Adding a new built-in framework is a config change, not a code change — this is the schema-driven pattern production LLM systems (Instructor, structured outputs) use.

This doc is for a developer who wants to add or modify a framework.

## How a framework is defined

A framework is a `FrameworkConfig` (see `backend/app/frameworks.py`):

```python
class Category(BaseModel):
    id: str           # "strengths", "political", etc. Short stable ID.
    name: str         # "Strengths" — human label.
    description: str  # What goes here — Claude reads this to cluster correctly.

class FrameworkConfig(BaseModel):
    id: str                                # "swot"
    name: str                              # "SWOT Analysis"
    description: str                       # Short context for the prompt.
    categories: list[Category]
```

The `description` field on each `Category` is the important part — Christian's *"beskrivning av innehållet"* feedback. Claude clusters based on what each category *means*, not just its label, so a good description directly improves accuracy.

## The built-in registry

Defined at the bottom of `frameworks.py`:

```python
_REGISTRY: dict[str, FrameworkConfig] = {
    "swot": SWOT,
    "pestel": PESTEL,
}
```

A session references a framework by its `id` (`"swot"`, `"pestel"`, or `"custom"`).

## Adding a new built-in framework

Say you want to add a **Start/Stop/Continue** framework as a built-in (currently it's only available via `custom` at session-creation time).

1. **Define the config** in `frameworks.py`, next to `SWOT` / `PESTEL`:

   ```python
   START_STOP_CONTINUE = FrameworkConfig(
       id="start_stop_continue",
       name="Start / Stop / Continue",
       description="A retrospective framework for team improvement actions.",
       categories=[
           Category(id="start", name="Start",
                    description="New activities or behaviours the team should begin."),
           Category(id="stop", name="Stop",
                    description="Activities that are no longer adding value and should cease."),
           Category(id="continue", name="Continue",
                    description="Things that are working well and should be maintained."),
       ],
   )
   ```

2. **Register it:**

   ```python
   _REGISTRY = {
       "swot": SWOT,
       "pestel": PESTEL,
       "start_stop_continue": START_STOP_CONTINUE,   # ← add this line
   }
   ```

That's it. The session-creation validator, the prompt builder, the PDF renderer, and the eval runner all pick it up automatically because they iterate `config.categories` dynamically. No other code changes.

3. **(Optional) Add eval cases** with `"framework": "start_stop_continue"` to `backend/eval/test_inputs.json` and run `python eval/run_eval.py --live` to measure accuracy for the new framework.

## Custom frameworks (facilitator-defined, no code)

A facilitator can define their own framework at session-creation time without touching code:

```json
POST /sessions
{
  "topic": "Q3 retrospective",
  "framework": "custom",
  "custom_categories": ["Wins", "Risks", "Actions"]
}
```

`build_custom_framework()` (in `frameworks.py`) turns the category names into a `FrameworkConfig` with auto-generated descriptions (`"Workshop ideas related to: <name>."`). The same code path handles it.

**Limitation:** custom-framework descriptions are auto-generated placeholders, not authored. Rich per-category descriptions (the thing that most improves accuracy) currently require a built-in framework entry. A UI for consultants to author descriptions is a flagged future improvement — see [`future_development.md`](future_development.md).

## How the framework reaches Claude

The prompt is built dynamically from the resolved `FrameworkConfig`:

```
Categories:
- strengths: Internal positive factors the organisation can leverage.
- weaknesses: Internal negative factors that hinder progress.
...
```

See [`prompt_design.md`](prompt_design.md) for the full prompt template and versioning. The category `id`s become the JSON keys Claude returns, which is how the eval scores accuracy (id-to-id comparison).

## Frameworks in the PDF

The report renderer (`pdf_service._build_category_grid`) reads the analysis result's `categories` dict dynamically and lays out a responsive grid (2 columns for ≤4 categories, 3 for 5+), cycling through an 8-colour palette. Adding a framework with 7 categories just works.
