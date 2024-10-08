"""edit token column name

Revision ID: d3dc067f3620
Revises: bfcd671bd96d
Create Date: 2024-10-01 10:02:37.787777

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3dc067f3620'
down_revision = 'bfcd671bd96d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('token', sa.Column('access_token', sa.String(), nullable=True))
    op.drop_column('token', 'token')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('token', sa.Column('token', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('token', 'access_token')
    # ### end Alembic commands ###
