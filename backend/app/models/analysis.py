from pydantic import BaseModel


class ClusteredIdea(BaseModel):
    idea_id: str
    summary: str


class AnalysisResult(BaseModel):
    session_id: str
    framework: str
    categories: dict[str, list[ClusteredIdea]]
    key_themes: list[str] = []
    decisions_made: list[str] = []
    open_questions: list[str] = []
    recommended_next_steps: list[str] = []
