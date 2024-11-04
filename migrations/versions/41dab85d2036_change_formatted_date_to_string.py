"""change formatted-date to string

Revision ID: 41dab85d2036
Revises: 969663a43a8d
Create Date: 2024-10-01 16:36:52.924452

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '41dab85d2036'
down_revision = '969663a43a8d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('event_info', 'formatted_date',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.String(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('event_info', 'formatted_date',
               existing_type=sa.String(),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
    # ### end Alembic commands ###