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
    camping_type = Column(Choice(c.CAMPING_TYPE_OPTS), default=c.TENT)
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
            new_cost = c.CABIN_TYPE_PRICES[kwargs['cabin_type']]

        return int(current_cost) * 100, (int(new_cost) * 100) - (int(current_cost) * 100)
    
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
            addon_list.append('{} brunch ticket(s) (${}/ticket)'.format(self.brunch_tickets, c.FOOD_PRICE))
        if self.dinner_tickets:
            addon_list.append('{} dinner ticket(s) (${}/ticket)'.format(self.dinner_tickets, c.FOOD_PRICE))
        if self.camping_type == c.CABIN:
            addon_list.append(self.cabin_type_label)
        elif int(c.CAMPING_TYPE_PRICES[self.camping_type]):
            addon_list.append('{}{}'.format(self.camping_type_label, ' parking pass' if self.camping_type in [c.CAR, c.RV] else ''))
        return addon_list