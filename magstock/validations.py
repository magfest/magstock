from wtforms import validators
from wtforms.validators import ValidationError, StopValidation

from .config import c
from uber.validations import Consents, PreregOtherInfo, PanelInfo, RoomLottery, DietaryRestrictions, JobInfo, JobTemplateInfo, TableInfo


def waiver_required(form):
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


Consents.field_validation.required_fields.update(required_waiver_fields)


Consents.field_validation.validations['acknowledged_checkin_policy']['optional'] = validators.Optional()
Consents.field_validation.validations['waiver_signature']['optional'] = validators.Optional()
Consents.field_validation.validations['waiver_date']['optional'] = validators.Optional()
Consents.field_validation.validations['waiver_consent']['optional'] = validators.Optional()


PreregOtherInfo.field_validation.required_fields.update(required_waiver_fields)


TableInfo.field_validation.required_fields['waitlist_notice'] = (
    "Please let us know the latest you are comfortable being pulled from the wait-list.",
    'waitlist_notice', lambda x: x.form.model.is_dealer)