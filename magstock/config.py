from os.path import join

from sideboard.lib import parse_config, request_cached_property
from uber.config import c, Config, dynamic
from uber.menu import MenuItem
from uber.models import Attendee, Session

from magstock._version import __version__  # noqa: F401

config = parse_config(__file__)
c.include_plugin_config(config)

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
        
    @property
    def CAMPING_TYPE_BUTTONS(self):
        # With apologies to future-me
        camping_types = {}
        camping_types[c.TENT] = ("Tent", c.CAMPING_TYPE_PRICES[c.TENT], "Included in your registration! Tent camping is first come, first serve.")
        camping_types[c.CAR] = ("Car", c.CAMPING_TYPE_PRICES[c.CAR], "Price is per vehicle.")
        camping_types[c.RV] = ("RV", c.CAMPING_TYPE_PRICES[c.RV], "Price is per vehicle, and there are no power or sewage hookups.")
        camping_types[c.CABIN] = ("Cabin ($600+)", c.CAMPING_TYPE_PRICES[c.CABIN], "Select a cabin option below. Cabins are limited availability.")
        return camping_types
    
    @request_cached_property
    @dynamic
    def CABIN_AVAILABILITY_MATRIX(self):
        cabins_left = {}
        with Session() as session:
            for cabin in c.CABIN_TYPES.keys():
                cabin_count = session.query(Attendee).filter_by(cabin_type=cabin).count()
                cabins_left[cabin] = max(0, int(c.CABIN_TYPE_STOCKS[cabin]) - cabin_count)
        return cabins_left

c.CABIN_TYPE_OPTS = [(key, '{} (${})'.format(desc, int(c.CABIN_TYPE_PRICES[key])) if int(c.CABIN_TYPE_PRICES.get(key, 0)) else desc) for key, desc in c.CABIN_TYPE_OPTS]