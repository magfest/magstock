from datetime import datetime

from os.path import join

from residue import CoerceUTF8 as UnicodeText
from sideboard.lib import parse_config
from sqlalchemy.types import Boolean, Date
from uber.config import c, Config
from uber.decorators import cost_property, prereg_validation, presave_adjustment, validation
from uber.menu import MenuItem
from uber.models import Choice, DefaultColumn as Column, Session
from uber.jinja import template_overrides
from uber.utils import add_opt, mount_site_sections, static_overrides

from magstock._version import __version__  # noqa: F401


config = parse_config(__file__)
c.include_plugin_config(config)
mount_site_sections(config['module_root'])
static_overrides(join(config['module_root'], 'static'))
template_overrides(join(config['module_root'], 'templates'))

c.MENU.append_menu_item(
    MenuItem(name='MAGStock', submenu=[
        MenuItem(name='Tent Groupings', href='../magstock/grouped'),
        MenuItem(name='Food Report', href='../magstock/food_consumers'),
        MenuItem(name='Campsite Assignments', href='../magstock/campsite_assignments'),
        MenuItem(name='Parking Info', href='../magstock/parking'),
    ])
)


@Config.mixin
class ExtraConfig:
    @property
    def FOOD_COUNT(self):
        with Session() as session:
            return len(session.food_consumers())

    @property
    def PREREG_DONATION_OPTS(self):
        """
        We're overriding this so that we can cut off Supporter registrations
        after we've sold a capped number and so that we can cut off shirt sales
        after the supporter deadline (MAGStock doesn't assume inventory risk on
        tshirts so they only sell them to people who preorder and do not sell
        any on-site).
        """
        if self.AFTER_SUPPORTER_DEADLINE:
            return [(amt, desc) for amt, desc in self.DONATION_TIER_OPTS if amt < self.SHIRT_LEVEL]
        elif not self.SUPPORTER_AVAILABLE:
            return [(amt, desc) for amt, desc in self.DONATION_TIER_OPTS if amt < self.SUPPORTER_LEVEL]
        else:
            return self.DONATION_TIER_OPTS


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
    allergies = Column(UnicodeText)
    coming_with = Column(UnicodeText)
    coming_as = Column(Choice(c.COMING_AS_OPTS), nullable=True)
    site_type = Column(Choice(c.SITE_TYPE_OPTS), nullable=True)
    noise_level = Column(Choice(c.NOISE_LEVEL_OPTS), nullable=True)
    camping_type = Column(Choice(c.CAMPING_TYPE_OPTS), nullable=True)
    purchased_food = Column(Boolean, default=False)
    license_plate = Column(UnicodeText, default='')
    site_number = Column(Choice(c.CAMPSITE_OPTS), nullable=True, admin_only=True)
    waiver_signature = Column(UnicodeText)
    waiver_consent = Column(Boolean, default=False)
    waiver_date = Column(Date, nullable=True, default=None)

    @cost_property
    def food_cost(self):
        return c.FOOD_PRICE if self.purchased_food else 0

    @property
    def auto_food(self):
        """
        :return: True if this Attendee automatically gets free food, False if not
        """
        return self.badge_type in [c.GUEST_BADGE] or hasattr(self, 'band') and self.band is not None

    @property
    def gets_food(self):
        return self.auto_food or self.purchased_food

    @presave_adjustment
    def free_food_only(self):
        """
        Fixes a problem where if someone was marked as purchasing food, they'd
        be stuck owing money for food even if they later qualified for free food.

        Returns:
            None
        """
        if self.auto_food:
            self.purchased_food = False

    @presave_adjustment
    def roughing_it(self):
        if self.site_type == c.PRIMITIVE:
            self.ribbon = add_opt(self.ribbon_ints, c.ROUGHING_IT)

    @property
    def addons(self):
        return ['Food all weekend'] if self.purchased_food else []


@validation.Attendee
def camping_checks(attendee):
    if not attendee.placeholder:
        if not attendee.noise_level:
            return 'Noise Level is a required field'
        elif not attendee.site_type:
            return 'Site Type is a required field'
        elif not attendee.camping_type:
            return 'Please tell us how you are camping'
        elif not attendee.coming_as:
            return 'Please tell us whether you are leading a group'
        elif not attendee.coming_with:
            if attendee.coming_as == c.TENT_LEADER:
                return 'Please tell us who is in your camping group'
            elif attendee.coming_as == c.TENT_FOLLOWER:
                return 'Please tell us who your camp leader is'


@prereg_validation.Attendee
def waiver_consent(attendee):
    if not attendee.waiver_signature:
        return 'You must sign your full legal name to consent to the waiver'
    elif attendee.waiver_signature != attendee.legal_first_name + ' ' + attendee.legal_last_name:
        return 'Your waiver signature must match your full legal name, {}'.format(
            attendee.legal_first_name + ' ' + attendee.legal_last_name)
    elif not attendee.waiver_consent:
        return 'You must check the waiver consent checkbox'
    elif attendee.waiver_date >= datetime.utcnow().date():
        return 'Your date of signature should be in the past'
