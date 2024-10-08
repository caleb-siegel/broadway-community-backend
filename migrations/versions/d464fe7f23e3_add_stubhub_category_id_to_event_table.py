"""add stubhub_category_id to event table

Revision ID: d464fe7f23e3
Revises: 8c02424b8f81
Create Date: 2024-10-01 11:13:31.648127

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd464fe7f23e3'
down_revision = '8c02424b8f81'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event', sa.Column('stubhub_category_id', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('event', 'stubhub_category_id')
    # ### end Alembic commands ###
