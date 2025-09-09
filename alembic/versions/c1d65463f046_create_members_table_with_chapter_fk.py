"""create members table with chapter FK

Revision ID: c1d65463f046
Revises: dc845ff4846f
Create Date: 2025-08-30 12:29:06.899344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d65463f046'
down_revision: Union[str, Sequence[str], None] = 'dc845ff4846f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
