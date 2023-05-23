from residue import CoerceUTF8 as UnicodeText
from sqlalchemy.types import Boolean, Date, Integer
from uber.api import AttendeeLookup
from uber.config import c
from uber.decorators import cost_property, presave_adjustment
from uber.models import Choice, DefaultColumn as Column, MultiChoice, Session
from uber.utils import add_opt

from magstock._version import __version__  # noqa: F401

AttendeeLookup.fields_full['gets_food'] = True

@Session.model_mixin
class SessionMixin:
    def food_consumers(self):
        """
        :return: list of anyone who gets food, regardless of if they're comp'd food or if they paid for it
        """
        return [a for a in self.query(Attendee).all() if a.gets_food]

    def food_purchasers(self):
        """
        :return: list of anyone who paid money to get food
        """
        return self.query(Attendee).filter(Attendee.purchased_food == True)  # noqa: E712


@Session.model_mixin
class Attendee:
    brunch_tickets = Column(Integer, default=0)
    dinner_tickets = Column(Integer, default=0)
    meal_restrictions = Column(MultiChoice(c.MEAL_TICKET_RESTRICTION_OPTS))
    camping_type = Column(Choice(c.CAMPING_TYPE_OPTS), default=c.TENT, nullable=True) # TODO: Make non-nullable next year BEFORE standing up servers
    cabin_type = Column(Choice(c.CABIN_TYPE_OPTS), nullable=True)
    license_plate = Column(UnicodeText, default='')
    site_number = Column(Choice(c.CAMPSITE_OPTS), nullable=True, admin_only=True)
    acknowledged_checkin_policy = Column(Boolean, default=False)
    waiver_signature = Column(UnicodeText)
    waiver_consent = Column(Boolean, default=False)
    waiver_date = Column(Date, nullable=True, default=None)
    
    def calc_meal_ticket_change(self, **kwargs):
        if 'brunch_tickets' in kwargs:
            current_cost = self.brunch_tickets * c.FOOD_PRICE * 100
            new_cost = int(kwargs['brunch_tickets']) * c.FOOD_PRICE * 100
        elif 'dinner_tickets' in kwargs:
            current_cost = self.dinner_tickets * c.FOOD_PRICE * 100
            new_cost = int(kwargs['dinner_tickets']) * c.FOOD_PRICE * 100

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
    
    @presave_adjustment
    def no_cabin_if_not_cabin_camping(self):
        if self.camping_type != c.CABIN:
            self.cabin_type = None

    @property
    def available_cabin_types(self):
        if self.cabin_type:
            return [(key, desc) for key, desc in c.CABIN_TYPE_OPTS if int(c.CABIN_TYPE_PRICES[key]) >= int(c.CABIN_TYPE_PRICES[self.cabin_type])]
        return c.CABIN_TYPE_OPTS

    @property
    def purchased_food(self):
        return self.brunch_tickets or self.dinner_tickets

    @property
    def auto_food(self):
        """
        :return: True if this Attendee automatically gets free food, False if not
        """
        return self.badge_type in [c.GUEST_BADGE] or hasattr(self, 'band') and self.band is not None

    @property
    def gets_food(self):
        return self.auto_food or self.purchased_food

    @property
    def addons(self):
        addon_list = []
        if self.brunch_tickets:
            addon_list.append('{} brunch ticket(s) (${} at ${}/ticket)'.format(self.brunch_tickets, self.brunch_tickets * c.FOOD_PRICE, c.FOOD_PRICE))
        if self.dinner_tickets:
            addon_list.append('{} dinner ticket(s) (${} at ${}/ticket)'.format(self.dinner_tickets, self.dinner_tickets * c.FOOD_PRICE, c.FOOD_PRICE))
        if self.camping_type and self.camping_type == c.CABIN and self.cabin_type:
            addon_list.append('{}'.format(self.cabin_type_label))
        elif self.camping_type and int(c.CAMPING_TYPE_PRICES[self.camping_type]):
            addon_list.append('{}{}{}'.format(self.camping_type_label,
                                            ' parking pass' if self.camping_type in [c.CAR, c.RV] else '',
                                            ' (${})'.format(c.CAMPING_TYPE_PRICES[self.camping_type]) if c.CAMPING_TYPE_PRICES[self.camping_type] else ''))
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
                or self.camping_type != c.TENT or self.cabin_type or self.brunch_tickets or self.dinner_tickets
    
    @property
    def shift_prereqs_complete(self):
        return not self.placeholder and (self.food_restrictions_filled_out or not c.PRE_CON) and (
            not c.VOLUNTEER_AGREEMENT_ENABLED or self.agreed_to_volunteer_agreement) and (
            not c.EMERGENCY_PROCEDURES_ENABLED or self.reviewed_emergency_procedures) \
            and c.SHIFTS_CREATED

    def undo_extras(self):
        if self.active_receipt:
            return "Could not undo extras, this attendee has an open receipt!"
        self.amount_extra = 0
        self.extra_donation = 0
        if self.badge_type in c.BADGE_TYPE_PRICES:
            self.badge_type = c.ATTENDEE_BADGE
        self.camping_type = c.TENT
        self.cabin_type = None
        self.brunch_tickets = 0
        self.dinner_tickets = 0


@Session.model_mixin
class Group:
    @property
    def dealer_badges_remaining(self):
        return 0