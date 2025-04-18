"""add email and sms to user table

Revision ID: 9b4036bf4a13
Revises: 093b308c04d8
Create Date: 2024-10-14 15:16:55.779535

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b4036bf4a13'
down_revision = '093b308c04d8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('email', sa.String(), nullable=True))
    op.add_column('user', sa.Column('phone_number', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'phone_number')
    op.drop_column('user', 'email')
    # ### end Alembic commands ###
