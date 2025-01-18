"""Add drawn_shapes to incidents

Revision ID: add_drawn_shapes
Revises: 58a64db92631
Create Date: 2025-01-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_drawn_shapes'
down_revision = '58a64db92631'
branch_labels = None
depends_on = None

def upgrade():
    # Add drawn_shapes column
    with op.batch_alter_table('incidents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('drawn_shapes', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('latitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('longitude', sa.Float(), nullable=True))

def downgrade():
    # Remove columns in reverse order
    with op.batch_alter_table('incidents', schema=None) as batch_op:
        batch_op.drop_column('longitude')
        batch_op.drop_column('latitude')
        batch_op.drop_column('drawn_shapes')
