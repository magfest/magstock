"""Update meal options

Revision ID: eb5471294a81
Revises: e175c87ef65b
Create Date: 2024-03-21 23:06:08.767747

"""


# revision identifiers, used by Alembic.
revision = 'eb5471294a81'
down_revision = 'e175c87ef65b'
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
    op.add_column('attendee', sa.Column('meal_plan', sa.Integer(), server_default='30893849', nullable=False))
    op.alter_column('attendee', 'camping_type',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('attendee', 'brunch_tickets')
    op.drop_column('attendee', 'dinner_tickets')


def downgrade():
    op.add_column('attendee', sa.Column('dinner_tickets', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False))
    op.add_column('attendee', sa.Column('brunch_tickets', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False))
    op.alter_column('attendee', 'camping_type',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_column('attendee', 'meal_plan')
