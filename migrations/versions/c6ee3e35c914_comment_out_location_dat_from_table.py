"""comment out location dat from table

Revision ID: c6ee3e35c914
Revises: 0fee087bbbf3
Create Date: 2024-11-26 11:26:30.005734

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c6ee3e35c914'
down_revision = '0fee087bbbf3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('event_info', 'location')
    op.drop_column('event_info', 'note')
    op.drop_column('event_info', 'quantity')
    op.drop_column('event_info', 'row')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event_info', sa.Column('row', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('event_info', sa.Column('quantity', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('event_info', sa.Column('note', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('event_info', sa.Column('location', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
