from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import Integer, Numeric, Date, Time, Boolean

# revision identifiers, used by Alembic.
revision = '725f2be0233c'
down_revision = '210d40ac7a10'
branch_labels = None
depends_on = None


def upgrade():
    # Create the new tables
    op.create_table('category_alert',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('price', sa.Numeric(scale=2), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('show_time', sa.Time(), nullable=True),
        sa.Column('send_email', sa.Boolean(), nullable=True),
        sa.Column('send_sms', sa.Boolean(), nullable=True),
        sa.Column('send_push', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['category.id'], name=op.f('fk_category_alert_category_id_category')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_category_alert_user_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_category_alert'))
    )
    op.create_table('event_alert',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('price', sa.Numeric(scale=2), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('show_time', sa.Time(), nullable=True),
        sa.Column('send_email', sa.Boolean(), nullable=True),
        sa.Column('send_sms', sa.Boolean(), nullable=True),
        sa.Column('send_push', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['event.id'], name=op.f('fk_event_alert_event_id_event')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_event_alert_user_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_event_alert'))
    )

    # Define old tables for data migration
    category_preference = table('category_preference',
        column('id', Integer),
        column('user_id', Integer),
        column('category_id', Integer),
        column('price', Numeric),
        column('start_date', Date),
        column('end_date', Date),
        column('show_time', Time),
        column('send_email', Boolean),
        column('send_sms', Boolean),
        column('send_push', Boolean)
    )
    event_preference = table('event_preference',
        column('id', Integer),
        column('user_id', Integer),
        column('event_id', Integer),
        column('price', Numeric),
        column('start_date', Date),
        column('end_date', Date),
        column('show_time', Time),
        column('send_email', Boolean),
        column('send_sms', Boolean),
        column('send_push', Boolean)
    )

    # Migrate data from old tables to new tables
    op.execute("""
        INSERT INTO category_alert (id, user_id, category_id, price, start_date, end_date, show_time, send_email, send_sms, send_push)
        SELECT id, user_id, category_id, price, start_date, end_date, show_time, send_email, send_sms, send_push
        FROM category_preference;
    """)

    op.execute("""
        INSERT INTO event_alert (id, user_id, event_id, price, start_date, end_date, show_time, send_email, send_sms, send_push)
        SELECT id, user_id, event_id, price, start_date, end_date, show_time, send_email, send_sms, send_push
        FROM event_preference;
    """)

    # Drop old tables
    op.drop_table('category_preference')
    op.drop_table('event_preference')


def downgrade():
    # Recreate the old tables
    op.create_table('category_preference',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('price', sa.Numeric(scale=2), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('show_time', sa.Time(), nullable=True),
        sa.Column('send_email', sa.Boolean(), nullable=True),
        sa.Column('send_sms', sa.Boolean(), nullable=True),
        sa.Column('send_push', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['category.id'], name='fk_category_preference_category_id_category'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_category_preference_user_id_user'),
        sa.PrimaryKeyConstraint('id', name='pk_category_preference')
    )
    op.create_table('event_preference',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('price', sa.Numeric(scale=2), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('show_time', sa.Time(), nullable=True),
        sa.Column('send_email', sa.Boolean(), nullable=True),
        sa.Column('send_sms', sa.Boolean(), nullable=True),
        sa.Column('send_push', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['event.id'], name='fk_event_preference_event_id_event'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_event_preference_user_id_user'),
        sa.PrimaryKeyConstraint('id', name='pk_event_preference')
    )

    # Migrate data back to old tables
    op.execute("""
        INSERT INTO category_preference (id, user_id, category_id, price, start_date, end_date, show_time, send_email, send_sms, send_push)
        SELECT id, user_id, category_id, price, start_date, end_date, show_time, send_email, send_sms, send_push
        FROM category_alert;
    """)

    op.execute("""
        INSERT INTO event_preference (id, user_id, event_id, price, start_date, end_date, show_time, send_email, send_sms, send_push)
        SELECT id, user_id, event_id, price, start_date, end_date, show_time, send_email, send_sms, send_push
        FROM event_alert;
    """)

    # Drop new tables
    op.drop_table('category_alert')
    op.drop_table('event_alert')