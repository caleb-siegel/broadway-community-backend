"""change weekday to integer

Revision ID: 093b308c04d8
Revises: 283c9409a039
Create Date: 2024-10-02 10:51:36.360065

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '093b308c04d8'
down_revision = '283c9409a039'
branch_labels = None
depends_on = None

def upgrade():
    # Step 1: Drop the old event_weekday column
    op.drop_column('event_info', 'event_weekday')

    # Step 2: Add a new event_weekday column as an integer
    op.add_column('event_info', sa.Column('event_weekday', sa.Integer(), nullable=True))

    # Step 3: Update the new event_weekday column with extracted weekdays
    op.execute("""
        UPDATE event_info
        SET event_weekday = EXTRACT(DOW FROM event_date)::INTEGER
    """)

def downgrade():
    # Optional: Drop the integer event_weekday column
    op.drop_column('event_info', 'event_weekday')

    # Add the old event_weekday column back as a DATE type if needed
    op.add_column('event_info', sa.Column('event_weekday', sa.Date(), nullable=True))