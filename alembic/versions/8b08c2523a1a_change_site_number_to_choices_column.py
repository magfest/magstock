"""Change site_number to Choices column

Revision ID: 8b08c2523a1a
Revises: 6a885e4ac48d
Create Date: 2016-06-16 04:08:27.579294

"""

# revision identifiers, used by Alembic.
revision = '8b08c2523a1a'
down_revision = '6a885e4ac48d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import sideboard


def upgrade():
    op.alter_column('attendee', 'site_number',
               existing_type=sa.VARCHAR(),
               nullable=True,
               existing_server_default=sa.text("''::character varying"))
    ### end Alembic commands ###


def downgrade():
    op.alter_column('attendee', 'site_number',
               existing_type=sa.VARCHAR(),
               nullable=False,
               existing_server_default=sa.text("''::character varying"))
    ### end Alembic commands ###
