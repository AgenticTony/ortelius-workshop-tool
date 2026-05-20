from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.models import AnalysisResult
from app.routes.sessions import sessions
from app.routes.ideas import ideas
from app.services.claude_service import analyse_ideas
from app.services.pdf_service import generate_pdf

router = APIRouter(tags=["analysis"])

analysis_results: dict[str, AnalysisResult] = {}


@router.post("/sessions/{session_id}/analyse", response_model=AnalysisResult)
def run_analysis(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_ideas = ideas.get(session_id, [])
    if not session_ideas:
        raise HTTPException(status_code=400, detail="No ideas to analyse")

    session = sessions[session_id]

    idea_dicts = [
        {
            "id": idea.id,
            "participant_id": idea.participant_id,
            "content": idea.content,
        }
        for idea in session_ideas
    ]

    result = analyse_ideas(session_id, session.framework, idea_dicts)
    analysis_results[session_id] = result
    return result


@router.get("/sessions/{session_id}/report")
def download_report(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    if session_id not in analysis_results:
        raise HTTPException(status_code=400, detail="No analysis found — run /analyse first")

    result = analysis_results[session_id]
    pdf_bytes = generate_pdf(result)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=workshop-report-{session_id}.pdf"},
    )
