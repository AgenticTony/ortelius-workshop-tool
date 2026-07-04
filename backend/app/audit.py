"""Structured audit logging for state-changing operations.

A dedicated logger (``audit``) lets ops route workshop mutations — who
created/joined/submitted/voted/analysed — to a separate, retained sink for
accountability, distinct from noisy application logs. Never logs secrets:
facilitator tokens are stored only as hashes, and participant tokens are not
logged. Participant names ARE recorded here on purpose (that's the point of an
audit trail) — protect the audit sink accordingly.
"""
import logging

audit_logger = logging.getLogger("audit")


def audit(
    action: str,
    *,
    session_id: str | None = None,
    actor: str = "anonymous",
    **fields: object,
) -> None:
    """Emit one structured audit line.

    Args:
        action: What happened, e.g. ``session_created``, ``idea_submitted``.
        session_id: The session the action affected (if any).
        actor: A non-secret identifier — ``"facilitator"``,
            ``"participant:<id>""``, or ``"system"``. Never a raw token.
        **fields: Extra key=value context (ids, framework, counts).
    """
    extra = " ".join(f"{k}={v}" for k, v in fields.items() if v is not None)
    audit_logger.info(
        "audit action=%s session=%s actor=%s%s%s",
        action,
        session_id,
        actor,
        " " if extra else "",
        extra,
    )
