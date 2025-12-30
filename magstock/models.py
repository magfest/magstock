from datetime import datetime

from residue import CoerceUTF8 as UnicodeText
from sqlalchemy.types import Boolean, Date, Integer
from uber.api import AttendeeLookup
from uber.config import c
from uber.decorators import cost_property, presave_adjustment
from uber.models import Choice, DefaultColumn as Column, MultiChoice, Session
from uber.utils import add_opt

from magstock._version import __version__  # noqa: F401

@Session.model_mixin
class Attendee:
    meal_plan = Column(Choice(c.MEAL_PLAN_OPTS), default=c.NO_FOOD)
    meal_restrictions = Column(MultiChoice(c.MEAL_TICKET_RESTRICTION_OPTS))
    camping_type = Column(Choice(c.CAMPING_TYPE_OPTS), default=c.TENT)
    cabin_type = Column(Choice(c.CABIN_TYPE_OPTS), nullable=True)
    license_plate = Column(UnicodeText, default='')
    acknowledged_checkin_policy = Column(Boolean, default=False)
    waiver_signature = Column(UnicodeText)
    waiver_consent = Column(Boolean, default=False)
    waiver_date = Column(Date, nullable=True, default=None)
    
    def calc_meal_plan_change(self, meal_plan):
        current_cost = int(c.MEAL_PLAN_PRICES[self.meal_plan]) * 100
        new_cost = int(c.MEAL_PLAN_PRICES[meal_plan]) * 100

        return current_cost, new_cost - current_cost

    def calc_camping_type_change(self, **kwargs):
        if 'camping_type' in kwargs:
            if kwargs['camping_type'] == c.CABIN:
                return 0, 0 # Skip this -- we'll handle it on the cabin side
            current_cost = c.CAMPING_TYPE_PRICES[self.camping_type]
            new_cost = c.CAMPING_TYPE_PRICES[kwargs['camping_type']]
        if 'cabin_type' in kwargs:
            if not self.cabin_type:
                current_cost = c.CAMPING_TYPE_PRICES[self.camping_type]
            else:
                current_cost = c.CABIN_TYPE_PRICES[self.cabin_type]
            if kwargs['cabin_type']:
                new_cost = c.CABIN_TYPE_PRICES[kwargs['cabin_type']]
            elif not self.cabin_type:
                new_cost = c.CAMPING_TYPE_PRICES[self.camping_type]
            else:
                new_cost = 0

        return int(current_cost) * 100, (int(new_cost) * 100) - (int(current_cost) * 100)

    def auto_update_receipt(self, params):
        if params.get('camping_type') and int(params['camping_type']) != c.CABIN:
            params['cabin_type'] = 0
        return params

    @presave_adjustment
    def no_cabin_if_not_cabin_camping(self):
        if self.camping_type != c.CABIN:
            self.cabin_type = None
    
    @presave_adjustment
    def meal_plan_if_guest(self):
        """
        if self.badge_type == c.GUEST_BADGE and (
                self.is_new or self.orig_value_of('badge_type') != c.GUEST_BADGE):
            self.meal_plan == c.BEVERAGE
        """
        pass

    @property
    def available_camping_type_opts(self):
        if self.is_new or self.camping_type == c.TENT or self.is_unpaid:
            return c.FORMATTED_CAMPING_TYPES

        if self.camping_type == c.CABIN:
            return [opt for opt in c.FORMATTED_CAMPING_TYPES if opt['value'] == c.CABIN]

        camping_type_opts = []

        for opt in c.FORMATTED_CAMPING_TYPES:
            if 'price' not in opt or int(c.CAMPING_TYPE_PRICES[self.camping_type]
                                         ) <= int(opt['price']) or opt['value'] == c.CABIN:
                camping_type_opts.append(opt)

        return camping_type_opts

    @property
    def available_cabin_types(self):
        cabin_opts = [(0, 'Please select a cabin type')]
        if self.cabin_type:
            return cabin_opts + [(key, desc) for key, desc in c.CABIN_TYPE_OPTS if int(c.CABIN_TYPE_PRICES[key]) >= int(c.CABIN_TYPE_PRICES[self.cabin_type])]
        return cabin_opts + c.CABIN_TYPE_OPTS

    @property
    def addons(self):
        addon_list = []
        if self.meal_plan and self.meal_plan != c.NO_FOOD:
            addon_list.append(f'{self.meal_plan_label} (${c.MEAL_PLAN_PRICES[self.meal_plan]})')
        if self.camping_type and self.camping_type == c.CABIN and self.cabin_type:
            addon_list.append(f'{self.cabin_type_label}')
        elif self.camping_type and int(c.CAMPING_TYPE_PRICES[self.camping_type]):
            addon_list.append('{}{}{}'.format(self.camping_type_label,
                                            ' Parking Pass' if self.camping_type in [c.CAR, c.RV] else '',
                                            ' (${})'.format(c.CAMPING_TYPE_PRICES[self.camping_type])))
        return addon_list
    
    @property
    def donation_swag(self):
        donation_items = []
        if self.amount_extra:
            donation_items.append('{} (${})'.format(c.DONATION_TIERS[self.amount_extra], self.amount_extra))
        extra_donations = ['Extra donation of ${}'.format(self.extra_donation)] if self.extra_donation else []
        return donation_items + extra_donations
    
    @property
    def has_extras(self):
        return self.amount_extra or self.extra_donation or self.badge_type in c.BADGE_TYPE_PRICES \
                or self.camping_type != c.TENT or self.cabin_type or self.meal_plan != c.NO_FOOD
    
    @property
    def shift_prereqs_complete(self):
        return not self.placeholder and (self.food_restrictions_filled_out or not c.PRE_CON) and (
            not c.VOLUNTEER_AGREEMENT_ENABLED or self.agreed_to_volunteer_agreement) and (
            not c.EMERGENCY_PROCEDURES_ENABLED or self.reviewed_emergency_procedures) \
            and c.AFTER_SHIFTS_CREATED

    def undo_extras(self):
        if self.active_receipt:
            return "Could not undo extras, this attendee has an open receipt!"
        self.amount_extra = 0
        self.extra_donation = 0
        if self.badge_type in c.BADGE_TYPE_PRICES:
            self.badge_type = c.ATTENDEE_BADGE
        self.camping_type = c.TENT
        self.cabin_type = None
        self.meal_plan = c.NO_FOOD


@Session.model_mixin
class Group:
    waitlist_notice = Column(Choice(c.DEALER_WAITLIST_OPTS), nullable=True)

    @property
    def dealer_badges_remaining(self):
        if self.status != c.APPROVED:
            return 0
        return 10
    
AttendeeLookup.fields_full['gets_food'] = True