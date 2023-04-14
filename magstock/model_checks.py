from datetime import datetime

from os.path import join

from residue import CoerceUTF8 as UnicodeText
from sideboard.lib import parse_config
from sqlalchemy.types import Boolean, Date
from uber.api import AttendeeLookup
from uber.config import c, Config
from uber.decorators import cost_property, prereg_validation, presave_adjustment, validation
from uber.menu import MenuItem
from uber.models import Choice, DefaultColumn as Column, Session
from uber.jinja import template_overrides
from uber.utils import add_opt, mount_site_sections, static_overrides

@validation.Attendee
def camping_checks(attendee):
    if not attendee.placeholder and not attendee.camping_type:
        return 'Please tell us how you are camping'


@prereg_validation.Attendee
def waiver_consent(attendee):
    if attendee.is_new or attendee.placeholder:
        if not attendee.waiver_signature:
            return 'You must sign your full legal name to consent to the waiver'
        elif attendee.waiver_signature != attendee.legal_first_name + ' ' + attendee.legal_last_name:
            return 'Your waiver signature must match your full legal name, {}'.format(
                attendee.legal_first_name + ' ' + attendee.legal_last_name)
        elif not attendee.waiver_consent:
            return 'You must check the waiver consent checkbox'
        elif attendee.waiver_date != datetime.utcnow().date():
            return 'Your date of signature should be today'


@prereg_validation.Attendee
def no_early_checkin(attendee):
    if (attendee.is_new or attendee.placeholder) and not attendee.acknowledged_checkin_policy:
        return 'You must acknowledge that early check-in is not possible.'
    

@validation.Attendee
def must_pick_cabin(attendee):
    if attendee.camping_type == c.CABIN and not attendee.cabin_type:
        return 'Please select a cabin type.'
    

@prereg_validation.Attendee
def cabin_sold_out(attendee):
    if (attendee.is_new or attendee.orig_value_of('cabin_type') != attendee.cabin_type) \
        and attendee.cabin_type and c.CABIN_AVAILABILITY_MATRIX[attendee.cabin_type] < 1:
        return "The type of cabin you have selected is sold out."


@validation.Attendee
def meal_tickets(attendee):
    if attendee.brunch_tickets < 0 or attendee.dinner_tickets < 0:
        return "You cannot buy negative meal tickets."