from wtforms import validators
from wtforms.validators import ValidationError, StopValidation

from .config import c
from uber.validations import Consents, BadgeExtras, PreregOtherInfo, PersonalInfo, TableInfo, ignore_unassigned_and_placeholders


def waiver_required(form):
    if form.is_admin:
        return False
    if type(form).__name__ == 'PreregOtherInfo' or (not form.model.is_new and form.model.badge_status != c.PENDING_STATUS):
        return True


required_waiver_fields = {
    'acknowledged_checkin_policy': ("You must acknowledge that early check-in is not possible.",
                                    'acknowledged_checkin_policy', lambda x: waiver_required(x.form)),
    'waiver_signature': ("You must sign your full legal name to consent to the waiver.",
                         'waiver_signature', lambda x: waiver_required(x.form)),
    'waiver_date': ("No date of signature. Please refresh the page or contact us.",
                    'waiver_date', lambda x: waiver_required(x.form)),
    'waiver_consent': ("You must check the waiver consent checkbox.",
                       'waiver_consent', lambda x: waiver_required(x.form)),    
    }


@BadgeExtras.field_validation('cabin_type')
def required_if_cabin(form, field):
    if form.camping_type.data and form.camping_type.data == c.CABIN and (not field.data or field.data == 0):
        raise ValidationError("Please select a cabin type.")


@BadgeExtras.new_or_changed('camping_type')
def car_or_rv_sold_out(form, field):
    if form.is_admin:
        return
    
    if field.data == c.CAR and c.CAR in c.SOLD_OUT_CAMPING_TYPES:
        raise ValidationError(f"Sorry, we're sold out of car camping spaces!")
    if field.data == c.RV and c.RV in c.SOLD_OUT_CAMPING_TYPES:
        raise ValidationError(f"Sorry, we're sold out of RV spaces!")


@BadgeExtras.new_or_changed('cabin_type')
def cabin_sold_out(form, field):
    if form.is_admin:
        return
    
    if field.data in field.get_sold_out_list():
        raise ValidationError(f"Sorry, we're sold out of {c.CABIN_TYPES[field.data].lower()}s!")


Consents.field_validation.required_fields.update(required_waiver_fields)


Consents.field_validation.validations['acknowledged_checkin_policy']['optional'] = validators.Optional()
Consents.field_validation.validations['waiver_signature']['optional'] = validators.Optional()
Consents.field_validation.validations['waiver_date']['optional'] = validators.Optional()
Consents.field_validation.validations['waiver_consent']['optional'] = validators.Optional()


@PersonalInfo.field_validation('cellphone')
@ignore_unassigned_and_placeholders
def cellphone_required(form, field):
    if not field.data and (not hasattr(form, 'copy_phone') or not form.copy_phone.data
            ) and not form.no_cellphone.data:
        raise ValidationError("Please provide a phone number.")


PreregOtherInfo.field_validation.required_fields.update(required_waiver_fields)


TableInfo.field_validation.required_fields['waitlist_notice'] = (
    "Please let us know the latest you are comfortable being pulled from the wait-list.",
    'waitlist_notice', lambda x: x.form.model.is_dealer)