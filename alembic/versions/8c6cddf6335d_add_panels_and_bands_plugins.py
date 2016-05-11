"""Add panels and bands plugins.

Revision ID: 8c6cddf6335d
Revises: 
Create Date: 2016-05-11 15:26:23.703464

"""

# revision identifiers, used by Alembic.
revision = '8c6cddf6335d'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import sideboard
import uber
from uber import c

def upgrade():
    op.create_table('event',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('location', uber.models.Choice(c.EVENT_LOCATION_OPTS), nullable=False),
    sa.Column('start_time', sideboard.lib.sa.UTCDateTime(), nullable=False),
    sa.Column('duration', sa.Integer(), nullable=False),
    sa.Column('name', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('description', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('band',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('group_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('event_id', sideboard.lib.sa.UUID(), nullable=True),
    sa.Column('payment', sa.Integer(), server_default='0', nullable=False),
    sa.Column('vehicles', sa.Integer(), server_default='1', nullable=False),
    sa.Column('estimated_loadin_minutes', sa.Integer(), server_default='60', nullable=False),
    sa.Column('estimated_performance_minutes', sa.Integer(), server_default='60', nullable=False),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ),
    sa.ForeignKeyConstraint(['group_id'], ['group.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('panel_application',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('event_id', sideboard.lib.sa.UUID(), nullable=True),
    sa.Column('name', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('length', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('description', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('unavailable', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('affiliations', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('past_attendance', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('presentation', uber.models.Choice(c.PRESENTATION_OPTS), nullable=False),
    sa.Column('other_presentation', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('tech_needs', uber.models.MultiChoice(c.TECH_NEED_OPTS), server_default='', nullable=False),
    sa.Column('other_tech_needs', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('applied', sideboard.lib.sa.UTCDateTime(), server_default=sa.text("timezone('utc', current_timestamp)"), nullable=False),
    sa.Column('status', uber.models.Choice(c.PANEL_APP_STATUS_OPTS), server_default='196944751', nullable=False),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('assigned_panelist',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('attendee_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('event_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['attendee_id'], ['attendee.id'], ondelete='cascade'),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('band_bio',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('band_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('desc', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('website', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('facebook', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('twitter', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('other_social_media', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('pic_filename', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('pic_content_type', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['band_id'], ['band.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('band_id')
    )
    op.create_table('band_charity',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('band_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('donating', uber.models.Choice(c.BAND_CHARITY_OPTS), nullable=True),
    sa.Column('desc', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['band_id'], ['band.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('band_id')
    )
    op.create_table('band_info',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('band_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('poc_phone', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('performer_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('bringing_vehicle', sa.Boolean(), server_default='False', nullable=False),
    sa.Column('vehicle_info', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('arrival_time', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['band_id'], ['band.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('band_id')
    )
    op.create_table('band_merch',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('band_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('selling_merch', uber.models.Choice(c.BAND_MERCH_OPTS), nullable=True),
    sa.ForeignKeyConstraint(['band_id'], ['band.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('band_id')
    )
    op.create_table('band_panel',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('band_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('wants_panel', uber.models.Choice(c.BAND_PANEL_OPTS), nullable=True),
    sa.Column('name', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('length', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('desc', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('tech_needs', uber.models.MultiChoice(c.TECH_NEED_OPTS), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['band_id'], ['band.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('band_id')
    )
    op.create_table('band_stage_plot',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('band_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('filename', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('content_type', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['band_id'], ['band.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('band_id')
    )
    op.create_table('band_taxes',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('band_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('w9_filename', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('w9_content_type', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['band_id'], ['band.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('band_id')
    )
    op.create_table('panel_applicant',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('app_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('submitter', sa.Boolean(), server_default='False', nullable=False),
    sa.Column('first_name', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('last_name', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('email', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.Column('cellphone', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['app_id'], ['panel_application.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('panel_vote',
    sa.Column('id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('app_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('account_id', sideboard.lib.sa.UUID(), nullable=False),
    sa.Column('vote', uber.models.Choice(c.PANEL_VOTE_OPTS), nullable=False),
    sa.Column('explanation', sideboard.lib.sa.CoerceUTF8(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['admin_account.id'], ondelete='cascade'),
    sa.ForeignKeyConstraint(['app_id'], ['panel_application.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    op.drop_table('panel_vote')
    op.drop_table('panel_applicant')
    op.drop_table('band_taxes')
    op.drop_table('band_stage_plot')
    op.drop_table('band_panel')
    op.drop_table('band_merch')
    op.drop_table('band_info')
    op.drop_table('band_charity')
    op.drop_table('band_bio')
    op.drop_table('assigned_panelist')
    op.drop_table('panel_application')
    op.drop_table('band')
    op.drop_table('event')
    ### end Alembic commands ###
