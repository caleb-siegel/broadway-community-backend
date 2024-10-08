"""change token to datetime

Revision ID: 08fd8db9e5d6
Revises: d3dc067f3620
Create Date: 2024-10-01 10:41:21.953674

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '08fd8db9e5d6'
down_revision = 'd3dc067f3620'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('token', 'expires_at',
               existing_type=sa.DATE(),
               type_=sa.DateTime(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('token', 'expires_at',
               existing_type=sa.DateTime(),
               type_=sa.DATE(),
               existing_nullable=True)
    # ### end Alembic commands ###
