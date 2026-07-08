"""dot_voting

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-08 12:00:00.000000

Adds dot-voting support:
  - new ``idea_votes`` association table (participant_id + idea_id, unique)
  - ``vote_budget`` column on ``sessions`` (default 3)

Note: existing ``ideas.votes`` counts are NOT backfilled into ``idea_votes`` —
there was no voter attribution before this migration, so we can't reconstruct
who voted. The aggregate count on the idea row is preserved as-is.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Vote budget per session (dot-voting). Default 3.
    op.add_column(
        'sessions',
        sa.Column('vote_budget', sa.Integer(), nullable=False, server_default='3'),
    )

    # Association table: one row per (participant, idea) vote.
    op.create_table(
        'idea_votes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('idea_id', sa.String(), nullable=False),
        sa.Column('participant_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['idea_id'], ['ideas.id']),
        sa.ForeignKeyConstraint(['participant_id'], ['participants.id']),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('participant_id', 'idea_id', name='uq_participant_idea_vote'),
    )
    op.create_index('ix_idea_votes_idea_id', 'idea_votes', ['idea_id'], unique=False)
    op.create_index('ix_idea_votes_participant_id', 'idea_votes', ['participant_id'], unique=False)
    op.create_index('ix_idea_votes_session_id', 'idea_votes', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_idea_votes_session_id', table_name='idea_votes')
    op.drop_index('ix_idea_votes_participant_id', table_name='idea_votes')
    op.drop_index('ix_idea_votes_idea_id', table_name='idea_votes')
    op.drop_table('idea_votes')
    op.drop_column('sessions', 'vote_budget')
