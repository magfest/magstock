"""Initial migration

Revision ID: bb334f039eac
Revises: 1ed43776064f
Create Date: 2017-04-24 09:30:24.914513

"""


# revision identifiers, used by Alembic.
revision = 'bb334f039eac'
down_revision = '1ed43776064f'
branch_labels = ('magstock',)
depends_on = None

from alembic import op
import sqlalchemy as sa



try:
    is_sqlite = op.get_context().dialect.name == 'sqlite'
except:
    is_sqlite = False

if is_sqlite:
    op.get_context().connection.execute('PRAGMA foreign_keys=ON;')
    utcnow_server_default = "(datetime('now', 'utc'))"
else:
    utcnow_server_default = "timezone('utc', current_timestamp)"


def upgrade():
    if is_sqlite:
        def listen_for_reflect(inspector, table, column_info):
            """Adds parenthesis around SQLite datetime defaults for utcnow."""
            if column_info['default'] == "datetime('now', 'utc')":
                column_info['default'] = utcnow_server_default

        with op.batch_alter_table(
                'attendee',
                reflect_kwargs=dict(listeners=[('column_reflect', listen_for_reflect)])) as batch_op:
            batch_op.add_column(sa.Column('allergies', sa.Unicode(), server_default='', nullable=False))
            batch_op.add_column(sa.Column('camping_type', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('coming_as', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('coming_with', sa.Unicode(), server_default='', nullable=False))
            batch_op.add_column(sa.Column('license_plate', sa.Unicode(), server_default='', nullable=False))
            batch_op.add_column(sa.Column('noise_level', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('site_number', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('site_type', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('purchased_food', sa.Boolean(), server_default='False', nullable=False))
    else:
        op.add_column('attendee', sa.Column('allergies', sa.Unicode(), server_default='', nullable=False))
        op.add_column('attendee', sa.Column('camping_type', sa.Integer(), nullable=True))
        op.add_column('attendee', sa.Column('coming_as', sa.Integer(), nullable=True))
        op.add_column('attendee', sa.Column('coming_with', sa.Unicode(), server_default='', nullable=False))
        op.add_column('attendee', sa.Column('license_plate', sa.Unicode(), server_default='', nullable=False))
        op.add_column('attendee', sa.Column('noise_level', sa.Integer(), nullable=True))
        op.add_column('attendee', sa.Column('site_number', sa.Integer(), nullable=True))
        op.add_column('attendee', sa.Column('site_type', sa.Integer(), nullable=True))
        op.add_column('attendee', sa.Column('purchased_food', sa.Boolean(), server_default='False', nullable=False))


def downgrade():
    op.drop_column('attendee', 'site_type')
    op.drop_column('attendee', 'site_number')
    op.drop_column('attendee', 'purchased_food')
    op.drop_column('attendee', 'noise_level')
    op.drop_column('attendee', 'license_plate')
    op.drop_column('attendee', 'coming_with')
    op.drop_column('attendee', 'coming_as')
    op.drop_column('attendee', 'camping_type')
    op.drop_column('attendee', 'allergies')
