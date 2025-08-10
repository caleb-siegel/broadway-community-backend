from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_weekday_to_alerts'
down_revision = 'acde7a8ea909'
branch_labels = None
depends_on = None


def upgrade():
    # Check if we're using PostgreSQL
    connection = op.get_bind()
    if connection.dialect.name == 'postgresql':
        # Add weekday column to event_alert table as ARRAY
        op.add_column('event_alert', sa.Column('weekday', postgresql.ARRAY(sa.Integer), nullable=True))
        
        # Add weekday column to category_alert table as ARRAY
        op.add_column('category_alert', sa.Column('weekday', postgresql.ARRAY(sa.Integer), nullable=True))
    else:
        # For non-PostgreSQL databases, use Text column
        op.add_column('event_alert', sa.Column('weekday', sa.Text, nullable=True))
        
        # Add weekday column to category_alert table as Text
        op.add_column('category_alert', sa.Column('weekday', sa.Text, nullable=True))


def downgrade():
    # Remove weekday column from event_alert table
    op.drop_column('event_alert', 'weekday')
    
    # Remove weekday column from category_alert table
    op.drop_column('category_alert', 'weekday') 