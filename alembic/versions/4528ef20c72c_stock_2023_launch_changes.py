"""Stock 2023 launch changes

Revision ID: 4528ef20c72c
Revises: c87aa6b37f39
Create Date: 2023-04-11 19:26:39.548258

"""


# revision identifiers, used by Alembic.
revision = '4528ef20c72c'
down_revision = 'c87aa6b37f39'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa



try:
    is_sqlite = op.get_context().dialect.name == 'sqlite'
except Exception:
    is_sqlite = False

if is_sqlite:
    op.get_context().connection.execute('PRAGMA foreign_keys=ON;')
    utcnow_server_default = "(datetime('now', 'utc'))"
else:
    utcnow_server_default = "timezone('utc', current_timestamp)"

def sqlite_column_reflect_listener(inspector, table, column_info):
    """Adds parenthesis around SQLite datetime defaults for utcnow."""
    if column_info['default'] == "datetime('now', 'utc')":
        column_info['default'] = utcnow_server_default

sqlite_reflect_kwargs = {
    'listeners': [('column_reflect', sqlite_column_reflect_listener)]
}

# ===========================================================================
# HOWTO: Handle alter statements in SQLite
#
# def upgrade():
#     if is_sqlite:
#         with op.batch_alter_table('table_name', reflect_kwargs=sqlite_reflect_kwargs) as batch_op:
#             batch_op.alter_column('column_name', type_=sa.Unicode(), server_default='', nullable=False)
#     else:
#         op.alter_column('table_name', 'column_name', type_=sa.Unicode(), server_default='', nullable=False)
#
# ===========================================================================


def upgrade():
    op.add_column('attendee', sa.Column('acknowledged_checkin_policy', sa.Boolean(), server_default='False', nullable=False))
    op.add_column('attendee', sa.Column('brunch_tickets', sa.Integer(), server_default='0', nullable=False))
    op.add_column('attendee', sa.Column('cabin_type', sa.Integer(), nullable=True))
    op.add_column('attendee', sa.Column('dinner_tickets', sa.Integer(), server_default='0', nullable=False))
    op.add_column('attendee', sa.Column('meal_restrictions', sa.Unicode(), server_default='', nullable=False))
    op.alter_column('attendee', 'camping_type',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('attendee', 'noise_level')
    op.drop_column('attendee', 'allergies')
    op.drop_column('attendee', 'coming_with')
    op.drop_column('attendee', 'purchased_food')
    op.drop_column('attendee', 'coming_as')
    op.drop_column('attendee', 'site_type')


def downgrade():
    op.add_column('attendee', sa.Column('site_type', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('attendee', sa.Column('coming_as', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('attendee', sa.Column('purchased_food', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False))
    op.add_column('attendee', sa.Column('coming_with', sa.VARCHAR(), server_default=sa.text("''::character varying"), autoincrement=False, nullable=False))
    op.add_column('attendee', sa.Column('allergies', sa.VARCHAR(), server_default=sa.text("''::character varying"), autoincrement=False, nullable=False))
    op.add_column('attendee', sa.Column('noise_level', sa.INTEGER(), autoincrement=False, nullable=True))
    op.alter_column('attendee', 'camping_type',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_column('attendee', 'meal_restrictions')
    op.drop_column('attendee', 'dinner_tickets')
    op.drop_column('attendee', 'cabin_type')
    op.drop_column('attendee', 'brunch_tickets')
    op.drop_column('attendee', 'acknowledged_checkin_policy')
