"""participant_session_id_index

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-04 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Speed up token verification, which filters participants by session_id
    # (resolve_principal). Without this, every authed idea/vote/SSE request on
    # a large session is a sequential scan.
    op.create_index(
        'ix_participants_session_id', 'participants', ['session_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_participants_session_id', table_name='participants')
