"""participant_token_hash

Revision ID: a1b2c3d4e5f6
Revises: 3e1ef3ddd0cb
Create Date: 2026-07-04 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '3e1ef3ddd0cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Participant bearer-token hash (issued at join; required to submit/vote/SSE).
    op.add_column('participants', sa.Column('token_hash', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('participants', 'token_hash')
