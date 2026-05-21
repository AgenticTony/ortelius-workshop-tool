from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session as DBSession

from app.dependencies import get_db
from app.models import AnalysisResult
from app.models.db_models import SessionDB, IdeaDB, AnalysisDB
from app.services.claude_service import analyse_ideas
from app.services.pdf_service import generate_pdf

router = APIRouter(tags=["analysis"])


@router.post("/sessions/{session_id}/analyse", response_model=AnalysisResult)
def run_analysis(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db_ideas = db.query(IdeaDB).filter(IdeaDB.session_id == session_id).all()
    if not db_ideas:
        raise HTTPException(status_code=400, detail="No ideas to analyse")

    idea_dicts = [
        {
            "id": idea.id,
            "participant_id": idea.participant_id,
            "participant_name": idea.participant_name,
            "content": idea.content,
        }
        for idea in db_ideas
    ]

    result = analyse_ideas(session_id, session.framework, idea_dicts)

    db_analysis = AnalysisDB(
        session_id=session_id,
        framework=result.framework,
        categories=result.categories.model_dump(),
        key_themes=result.key_themes,
        decisions_made=result.decisions_made,
        open_questions=result.open_questions,
        recommended_next_steps=result.recommended_next_steps,
    )
    db.add(db_analysis)
    db.flush()

    session.status = "analysed"
    db.commit()

    return result


@router.get("/sessions/{session_id}/analysis", response_model=AnalysisResult)
def get_analysis(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db_analysis = db.query(AnalysisDB).filter(AnalysisDB.session_id == session_id).first()
    if not db_analysis:
        raise HTTPException(status_code=404, detail="No analysis found — run POST /analyse first")

    return AnalysisResult(
        session_id=session_id,
        framework=db_analysis.framework,
        categories=db_analysis.categories,
        key_themes=db_analysis.key_themes,
        decisions_made=db_analysis.decisions_made,
        open_questions=db_analysis.open_questions,
        recommended_next_steps=db_analysis.recommended_next_steps,
    )


@router.get("/sessions/{session_id}/report")
def download_report(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db_analysis = db.query(AnalysisDB).filter(AnalysisDB.session_id == session_id).first()
    if not db_analysis:
        raise HTTPException(status_code=400, detail="No analysis found — run /analyse first")

    result = AnalysisResult(
        session_id=session_id,
        framework=db_analysis.framework,
        categories=db_analysis.categories,
        key_themes=db_analysis.key_themes,
        decisions_made=db_analysis.decisions_made,
        open_questions=db_analysis.open_questions,
        recommended_next_steps=db_analysis.recommended_next_steps,
    )

    pdf_bytes = generate_pdf(result)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=workshop-report-{session_id}.pdf"},
    )
