import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session as DBSession

from app.dependencies import Principal, get_db, get_event_bus, get_principal
from app.errors import (
    AlreadyVotedError,
    ForbiddenError,
    IdeaNotFoundError,
    NotVotedError,
    SessionNotFoundError,
    VoteBudgetExceededError,
)
from app.models import Idea, IdeaCreate
from app.models.db_models import IdeaDB, IdeaVoteDB, ParticipantDB, SessionDB
from app.rate_limit import limiter
from app.services.event_bus import EVENT_IDEA_ADDED, EVENT_IDEA_VOTED, EventBusProtocol

router = APIRouter(prefix="/sessions/{session_id}/ideas", tags=["ideas"])


@router.post("", response_model=Idea)
@limiter.limit("30/minute")
def submit_idea(
    request: Request,
    session_id: str,
    body: IdeaCreate,
    principal: Principal = Depends(get_principal),
    db: DBSession = Depends(get_db),
    bus: EventBusProtocol = Depends(get_event_bus),
):
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise SessionNotFoundError(session_id)

    # Author is the authenticated participant — ignore any client-supplied id
    # so a participant can't post under another's identity. A facilitator (no
    # participant_id) may seed ideas using the body's fields.
    if principal.participant_id:
        participant = (
            db.query(ParticipantDB).filter(ParticipantDB.id == principal.participant_id).first()
        )
        author_id = principal.participant_id
        author_name = participant.name if participant else body.participant_name
    else:
        author_id = body.participant_id
        author_name = body.participant_name

    idea = IdeaDB(
        session_id=session_id,
        participant_id=author_id,
        participant_name=author_name,
        content=body.content,
        category=body.category,
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)

    # Notify live listeners (SSE) that a new idea landed.
    bus.publish(session_id, EVENT_IDEA_ADDED, _idea_to_dict(idea))
    return _to_idea(idea)


@router.get("", response_model=list[Idea])
def list_ideas(
    session_id: str,
    principal: Principal = Depends(get_principal),
    db: DBSession = Depends(get_db),
):
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise SessionNotFoundError(session_id)
    ideas = db.query(IdeaDB).filter(IdeaDB.session_id == session_id).all()
    # Compute voted_by_me for the calling participant (facilitator → always False).
    voted_ids: set[str] = set()
    if principal.participant_id:
        voted_ids = {
            vid
            for (vid,) in db.query(IdeaVoteDB.idea_id)
            .filter(IdeaVoteDB.participant_id == principal.participant_id)
            .all()
        }
    return [_to_idea(idea, voted_by_me=(idea.id in voted_ids)) for idea in ideas]


@router.post("/{idea_id}/vote", response_model=Idea)
def vote_idea(
    session_id: str,
    idea_id: str,
    principal: Principal = Depends(get_principal),
    db: DBSession = Depends(get_db),
    bus: EventBusProtocol = Depends(get_event_bus),
):
    """Cast a dot-vote for an idea (one per participant per idea).

    Enforces the session's vote budget: a participant who has already cast
    ``vote_budget`` votes gets 409. Re-voting the same idea is 409 (use DELETE
    to un-vote first). Facilitators can't vote (403).
    """
    if not principal.participant_id:
        raise ForbiddenError("Only participants can vote. Facilitators cannot.")

    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise SessionNotFoundError(session_id)

    idea = (
        db.query(IdeaDB)
        .filter(IdeaDB.id == idea_id, IdeaDB.session_id == session_id)
        .first()
    )
    if not idea:
        raise IdeaNotFoundError(idea_id)

    # Already voted on this idea? 409 — no double-counting.
    existing = (
        db.query(IdeaVoteDB)
        .filter(
            IdeaVoteDB.participant_id == principal.participant_id,
            IdeaVoteDB.idea_id == idea_id,
        )
        .first()
    )
    if existing:
        raise AlreadyVotedError()

    # Budget check: how many has this participant cast across the session?
    used = (
        db.query(IdeaVoteDB)
        .filter(IdeaVoteDB.participant_id == principal.participant_id)
        .count()
    )
    if used >= session.vote_budget:
        raise VoteBudgetExceededError(
            f"You've used all {session.vote_budget} of your votes for this session."
        )

    # Record the vote + bump the denormalized count atomically.
    db.add(IdeaVoteDB(
        idea_id=idea_id,
        participant_id=principal.participant_id,
        session_id=session_id,
    ))
    idea.votes += 1
    db.commit()
    db.refresh(idea)

    bus.publish(session_id, EVENT_IDEA_VOTED, {
        "idea_id": idea.id,
        "votes": idea.votes,
        "voter_id": principal.participant_id,
        "action": "vote",
    })
    return _to_idea(idea, voted_by_me=True)


@router.delete("/{idea_id}/vote", response_model=Idea)
def unvote_idea(
    session_id: str,
    idea_id: str,
    principal: Principal = Depends(get_principal),
    db: DBSession = Depends(get_db),
    bus: EventBusProtocol = Depends(get_event_bus),
):
    """Remove a dot-vote (toggles off a prior POST). Restores one unit of budget."""
    if not principal.participant_id:
        raise ForbiddenError("Only participants can vote. Facilitators cannot.")

    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise SessionNotFoundError(session_id)

    idea = (
        db.query(IdeaDB)
        .filter(IdeaDB.id == idea_id, IdeaDB.session_id == session_id)
        .first()
    )
    if not idea:
        raise IdeaNotFoundError(idea_id)

    vote = (
        db.query(IdeaVoteDB)
        .filter(
            IdeaVoteDB.participant_id == principal.participant_id,
            IdeaVoteDB.idea_id == idea_id,
        )
        .first()
    )
    if not vote:
        raise NotVotedError()

    db.delete(vote)
    # Guard against the count going negative if the idea row and votes table
    # ever drift (defensive — should never happen given the unique constraint).
    idea.votes = max(0, idea.votes - 1)
    db.commit()
    db.refresh(idea)

    bus.publish(session_id, EVENT_IDEA_VOTED, {
        "idea_id": idea.id,
        "votes": idea.votes,
        "voter_id": principal.participant_id,
        "action": "unvote",
    })
    return _to_idea(idea, voted_by_me=False)


def _to_idea(idea: IdeaDB, voted_by_me: bool = False) -> Idea:
    return Idea(
        id=idea.id,
        session_id=idea.session_id,
        participant_id=idea.participant_id,
        participant_name=idea.participant_name,
        category=idea.category,
        content=idea.content,
        votes=idea.votes,
        created_at=idea.created_at,
        voted_by_me=voted_by_me,
    )


def _idea_to_dict(idea: IdeaDB) -> dict:
    """Serialize an idea for SSE payloads (JSON-safe)."""
    return {
        "id": idea.id,
        "session_id": idea.session_id,
        "participant_id": idea.participant_id,
        "participant_name": idea.participant_name,
        "category": idea.category,
        "content": idea.content,
        "votes": idea.votes,
        "created_at": idea.created_at.isoformat() if idea.created_at else None,
    }


# Re-exported for the stream router so SSE payloads share one serializer.
idea_payload = _idea_to_dict


def _dumps_event(payload: dict) -> str:
    return json.dumps(payload, default=str)
