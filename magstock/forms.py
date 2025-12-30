import cherrypy

from markupsafe import Markup
from wtforms import (BooleanField, DateField, EmailField, Form, FormField,
                     HiddenField, SelectField, SelectMultipleField, IntegerField,
                     StringField, TelField, validators, TextAreaField)
from wtforms.validators import ValidationError, StopValidation
from wtforms.widgets import html_params
from pockets.autolog import log

from uber.config import c
from uber.forms import (CustomValidation, MagForm, HiddenBoolField, HiddenIntField, SelectAvailableField, MultiCheckbox)
from uber.custom_tags import popup_link, format_currency, pluralize, table_prices, email_to_link


@MagForm.form_mixin
class PersonalInfo:
    license_plate = StringField('License Plate #', render_kw={'placeholder': 'XXX-XXXX'})
    badge_printed_name = HiddenField('Badge Printed Name (Unused)')

    def onsite_contact_label(self):
        return "MAGBuddy"

    def license_plate_desc(self):
        return ("Get through registration faster on-site! If you don't know which vehicle you'll be using, "
                "you can come back and update this later.")


@MagForm.form_mixin
class BadgeExtras:
    field_validation, new_or_changed_validation = CustomValidation(), CustomValidation()

    camping_type = HiddenIntField('How are you camping?')
    cabin_type = SelectAvailableField('Cabin Type',
                                      choices=[(0, 'Please select a cabin type')] + c.CABIN_TYPE_OPTS,
                                      default=0, coerce=int,
                                      sold_out_list_func=lambda: [cabin for cabin in c.CABIN_AVAILABILITY_MATRIX
                                                                  if c.CABIN_AVAILABILITY_MATRIX[cabin] < 1])
    meal_plan = HiddenIntField('Beverage/Meal Plan')
    meal_restrictions = SelectMultipleField('Dietary Restrictions', choices=c.MEAL_TICKET_RESTRICTION_OPTS,
                                            coerce=int, widget=MultiCheckbox(),
                                            description="Ramblewood's kitchen labels allergens at meals "
                                            "but can only specifically accommodate the above restrictions.")

    def camping_type_desc(self):
        return Markup(
            'Car and RV camping is restricted to a field adjacent to the communal bathrooms. '
            'Please review the information about camping options, including cabin type descriptions, '
            '<a href="https://magstock.org/camping-info/" target="_blank">on our website</a>.')
    
    def shirt_desc(self):
        return popup_link("../static/swag/shirt_guide.png", "[size guide]")

    @field_validation.cabin_type
    def required_if_cabin(form, field):
        if form.camping_type.data and form.camping_type.data == c.CABIN and (not field.data or field.data == 0):
            raise ValidationError("Please select a cabin type.")

    @new_or_changed_validation.camping_type
    def car_or_rv_sold_out(form, field):
        if field.data == c.CAR and c.CAR in c.SOLD_OUT_CAMPING_TYPES:
            raise ValidationError(f"Sorry, we're sold out of car camping spaces!")
        if field.data == c.RV and c.RV in c.SOLD_OUT_CAMPING_TYPES:
            raise ValidationError(f"Sorry, we're sold out of RV spaces!")

    @new_or_changed_validation.cabin_type
    def cabin_sold_out(form, field):
        if field.data in field.get_sold_out_list():
            raise ValidationError(f"Sorry, we're sold out of {c.CABIN_TYPES[field.data].lower()}s!")


@MagForm.form_mixin
class AdminBadgeExtras:
    camping_type = SelectField('Camping Type', coerce=int, choices=c.CAMPING_TYPE_OPTS)
    meal_plan = SelectField('Beverage/Meal Plan', coerce=int, choices=c.MEAL_PLAN_OPTS)


@MagForm.form_mixin
class Consents:
    acknowledged_checkin_policy = BooleanField(
        Markup('<strong>I acknowledge that there is NO early check-in and if I show up on Wednesday night '
               'then I will probably be asked to leave the campground.</strong>'))
    waiver_signature = StringField('Electronic Signature')
    waiver_date = DateField('Date of Signature', render_kw={'readonly': True, 'tabIndex': -1})
    waiver_consent = BooleanField(
        Markup('<strong>Yes</strong>, I understand that checking this box constitutes a legal signature '
               'confirming that I acknowledge and agree to the above waiver.'))

    def get_non_admin_locked_fields(self, attendee):
        if attendee.needs_pii_consent:
            return []

        return ['pii_consent', 'acknowledged_checkin_policy', 'waiver_date', 'waiver_signature', 'waiver_consent']


@MagForm.form_mixin
class AdminConsents:
    waiver_date = DateField('Date of Signature')


@MagForm.form_mixin
class PreregOtherInfo:
    first_name = HiddenField('First Name')
    last_name = HiddenField('Last Name')
    legal_name = HiddenField('Legal Name')
    acknowledged_checkin_policy = Consents.acknowledged_checkin_policy
    waiver_signature = Consents.waiver_signature
    waiver_date = Consents.waiver_date
    waiver_consent = Consents.waiver_consent

    def staffing_label(self):
        return ("We already have enough volunteers to run MAGStock this year. If you'd like to be added "
                "to our waitlist, click here and indicate your areas of interest. If we can accommodate more "
                "volunteers, Staffing Operations will reach out to you in mid-May.")


@MagForm.form_mixin
class TableInfo:
    waitlist_notice = SelectField('How close to the event are you comfortable being pulled from the wait-list?',
                                  coerce=int, choices=[(0, 'Please select an option')] + c.DEALER_WAITLIST_OPTS)


@MagForm.form_mixin
class CheckInForm:
    camping_type = HiddenField('Camping Type')
    cabin_type = HiddenField('Cabin Type')
    meal_plan = HiddenField('Meal Plan')
    license_plate = PersonalInfo.license_plate
