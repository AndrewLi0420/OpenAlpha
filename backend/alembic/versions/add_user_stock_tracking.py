"""Add user_stock_tracking table

Revision ID: add_user_stock_tracking
Revises: ed366b9039e4
Create Date: 2025-01-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_user_stock_tracking'
down_revision: Union[str, Sequence[str], None] = 'ed366b9039e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create user_stock_tracking table
    op.create_table('user_stock_tracking',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('stock_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_stock_tracking_user_id', 'user_stock_tracking', ['user_id'], unique=False)
    op.create_unique_constraint('uq_user_stock_tracking_user_stock', 'user_stock_tracking', ['user_id', 'stock_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_user_stock_tracking_user_stock', 'user_stock_tracking', type_='unique')
    op.drop_index('ix_user_stock_tracking_user_id', table_name='user_stock_tracking')
    op.drop_table('user_stock_tracking')

