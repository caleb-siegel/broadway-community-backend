"""add average calc to event_info table

Revision ID: ffc655aa71c7
Revises: c6ee3e35c914
Create Date: 2024-12-01 10:20:17.330769

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ffc655aa71c7'
down_revision = 'c6ee3e35c914'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event_info', sa.Column('average_denominator', sa.Integer(), nullable=True))
    op.add_column('event_info', sa.Column('average_lowest_price', sa.Numeric(scale=2), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('event_info', 'average_lowest_price')
    op.drop_column('event_info', 'average_denominator')
    # ### end Alembic commands ###
