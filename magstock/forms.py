import cherrypy

from markupsafe import Markup
from wtforms import (BooleanField, DateField, EmailField, Form, FormField,
                     HiddenField, SelectField, SelectMultipleField, IntegerField,
                     StringField, TelField, validators, TextAreaField)
from wtforms.validators import ValidationError, StopValidation
from wtforms.widgets import html_params
from pockets.autolog import log

from uber.config import c
from uber.forms import (AddressForm, NumberInputGroup, MagForm, IntSelect, SwitchInput, HiddenIntField, SelectAvailableField, CustomValidation)
from uber.custom_tags import popup_link, format_currency, pluralize, table_prices, email_to_link


@MagForm.form_mixin
class PersonalInfo:
    license_plate = StringField('License Plate #', render_kw={'placeholder': 'XXX-XXXX'})
    badge_printed_name = HiddenField('Badge Printed Name (Unused)')

    def get_optional_fields(self, attendee, is_admin=False):
        optional_list = self.super_get_optional_fields(attendee, is_admin)

        # This field is disabled/hidden, so it's never required
        optional_list.append('badge_printed_name')
        return optional_list

    def onsite_contact_label(self):
        return "MAGBuddy"

    def license_plate_desc(self):
        return ("Get through registration faster on-site! If you don't know which vehicle you'll be using, "
                "you can come back and update this later.")


@MagForm.form_mixin
class BadgeExtras:
    camping_type = HiddenIntField('How are you camping?')
    cabin_type = SelectAvailableField('Cabin Type',
                                      choices=[(0, 'Please select a cabin type')] + c.CABIN_TYPE_OPTS,
                                      default=0, coerce=int,
                                      sold_out_list_func=lambda: [cabin for cabin in c.CABIN_AVAILABILITY_MATRIX
                                                                  if c.CABIN_AVAILABILITY_MATRIX[cabin] < 1])
    # Meal tickets go here

    def camping_type_desc(self):
        return Markup(
            'Car and RV camping is restricted to a field adjacent to the communal bathrooms. '
            'Please review the information about camping options, including cabin type descriptions, '
            '<a href="https://magstock.org/camping-info/" target="_blank">on our website</a>.')


@MagForm.form_mixin
class Consents:
    acknowledged_checkin_policy = BooleanField(
        Markup('<strong>I acknowledge that there is NO early check-in and if I show up on Wednesday night '
               'then I will probably be asked to leave the campground.</strong>'),
        validators=[validators.InputRequired("You must acknowledge that early check-in is not possible.")])
    waiver_signature = StringField(
        'Electronic Signature',
        validators=[validators.DataRequired("You must sign your full legal name to consent to the waiver.")])
    waiver_date_display = DateField('Date of Signature', render_kw={'disabled': True})
    waiver_date = HiddenField('Date of Signature (UTC)',
                              validators=[validators.DataRequired("No date of signature. "
                                                                  "Please refresh the page or contact us.")])
    waiver_consent = BooleanField(
        Markup('<strong>Yes</strong>, I understand that checking this box constitutes a legal signature '
               'confirming that I acknowledge and agree to the above waiver.'),
               validators=[validators.InputRequired("You must check the waiver consent checkbox.")])

    def get_non_admin_locked_fields(self, attendee):
        if attendee.needs_pii_consent:
            return []

        return ['pii_consent', 'acknowledged_checkin_policy', 'waiver_date', 'waiver_signature', 'waiver_consent']
    
    def get_optional_fields(self, attendee, is_admin=False):
        optional_fields = self.super_get_optional_fields(attendee, is_admin)

        if (attendee.is_new or attendee.badge_status == c.PENDING_STATUS) or (
                attendee.valid_placeholder and cherrypy.request.method == 'POST'):
            optional_fields.extend(['acknowledged_checkin_policy', 'waiver_date',
                                    'waiver_signature', 'waiver_consent'])

        return optional_fields


@MagForm.form_mixin
class PreregOtherInfo:
    first_name = HiddenField('First Name')
    last_name = HiddenField('Last Name')
    acknowledged_checkin_policy = Consents.acknowledged_checkin_policy
    waiver_signature = Consents.waiver_signature
    waiver_date_display = Consents.waiver_date_display
    waiver_date = Consents.waiver_date
    waiver_consent = Consents.waiver_consent