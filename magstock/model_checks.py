from datetime import datetime

from os.path import join

from residue import CoerceUTF8 as UnicodeText
from sqlalchemy.types import Boolean, Date
from uber.api import AttendeeLookup
from uber.config import c, Config
from uber.decorators import cost_property, prereg_validation, presave_adjustment, validation
from uber.menu import MenuItem
from uber.models import Choice, DefaultColumn as Column, Session
from uber.jinja import template_overrides
from uber.utils import add_opt, mount_site_sections, static_overrides, localized_now


@prereg_validation.Attendee
def waiver_consent(attendee):
    if attendee.is_new or attendee.placeholder:
        if attendee.waiver_signature and attendee.waiver_signature != attendee.legal_first_name + ' ' + attendee.legal_last_name:
            return 'Your waiver signature must match your full legal name, {}'.format(
                attendee.legal_first_name + ' ' + attendee.legal_last_name)
        elif attendee.waiver_date and attendee.waiver_date != localized_now().date():
            return 'Your date of signature should be today'
