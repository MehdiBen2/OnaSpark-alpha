"""Add epuration_type to Infrastructures

Revision ID: add_epuration_type
Revises: 
Create Date: 2025-01-29

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_epuration_type'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Add epuration_type column to infrastructures table."""
    with op.batch_alter_table('infrastructures', schema=None) as batch_op:
        batch_op.add_column(sa.Column('epuration_type', sa.String(length=100), nullable=True, index=True))

def downgrade():
    """Remove epuration_type column from infrastructures table."""
    with op.batch_alter_table('infrastructures', schema=None) as batch_op:
        batch_op.drop_column('epuration_type')
