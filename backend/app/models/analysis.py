from pydantic import BaseModel


class ClusteredIdea(BaseModel):
    idea_id: str
    summary: str


class SwotCategories(BaseModel):
    strengths: list[ClusteredIdea] = []
    weaknesses: list[ClusteredIdea] = []
    opportunities: list[ClusteredIdea] = []
    threats: list[ClusteredIdea] = []


class AnalysisResult(BaseModel):
    session_id: str
    framework: str
    categories: SwotCategories
    key_themes: list[str] = []
    decisions_made: list[str] = []
    open_questions: list[str] = []
    recommended_next_steps: list[str] = []
