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
        MenuItem(name='Add-Ons Purchased', href='../magstock/addons'),
        MenuItem(name='Tent Groupings', href='../magstock/grouped'),
        MenuItem(name='Food Report', href='../magstock/food_consumers'),
        MenuItem(name='Campsite Assignments', href='../magstock/campsite_assignments'),
        MenuItem(name='Parking Info', href='../magstock/parking'),
    ])
)


@Config.mixin
class ExtraConfig:
    @property
    def FORMATTED_CAMPING_TYPES(self):
        # Returns camping type options for the 'card_select' form macro.

        return [
            {'name': 'Tent', 'icon': '', 'link': '', 'value': c.TENT, 'price': 0,
             'desc': 'Included in your registration! Tent camping is first come, first serve.'},
            {'name': 'Car', 'icon': '', 'link': '', 'value': c.CAR, 'price': c.CAMPING_TYPE_PRICES[c.CAR],
             'desc': 'Price is per vehicle.'},
            {'name': 'RV', 'icon': '', 'link': '', 'value': c.RV, 'price': c.CAMPING_TYPE_PRICES[c.RV],
             'desc': 'Price is per vehicle, and there are no power or sewage hookups.'},
            {'name': 'Cabin ($600+)', 'icon': '', 'link': '', 'value': c.CABIN,
             'price': 0,
             'desc': 'Select a cabin option below. Cabins are limited availability.'}
        ]
    
    @property
    def CAMPING_TYPE_BUTTONS(self):
        # With apologies to future-me
        camping_types = {}
        camping_types[c.TENT] = ("Tent", c.CAMPING_TYPE_PRICES[c.TENT], "Included in your registration! Tent camping is first come, first serve.")
        camping_types[c.CAR] = ("Car", c.CAMPING_TYPE_PRICES[c.CAR], "Price is per vehicle.")
        camping_types[c.RV] = ("RV", c.CAMPING_TYPE_PRICES[c.RV], "Price is per vehicle, and there are no power or sewage hookups.")
        camping_types[c.CABIN] = ("Cabin ($600+)", c.CAMPING_TYPE_PRICES[c.CABIN], "Select a cabin option below. Cabins are limited availability.")
        return camping_types
    
    @property
    def CAMPING_CABIN_TYPES(self):
        # For use with camping and cabin-related cost changes
        return {**c.CAMPING_TYPES, **c.CABIN_TYPES}

    @property
    def MEAL_TICKETS(self):
        # Similar to the above, this is so our cost change system can accurately report how many brunch/dinner tickets you're buying
        num_dict = {}
        for i in range(1, 11):
            num_dict[i] = str(i)
        return num_dict
    
    @request_cached_property
    @dynamic
    def CAMPING_TYPES_BOUGHT(self):
        camping_types = {}
        with Session() as session:
            for type in c.CAMPING_TYPES.keys():
                camping_types[type] = session.valid_attendees().filter_by(camping_type=type).count()
        return camping_types
    
    @request_cached_property
    @dynamic
    def CABIN_TYPES_BOUGHT(self):
        cabin_types = {}
        with Session() as session:
            for type in c.CABIN_TYPES.keys():
                cabin_types[type] = session.valid_attendees().filter_by(cabin_type=type).count()
        return cabin_types

    @property
    def CABIN_AVAILABILITY_MATRIX(self):
        cabins_left = {}
        for type in c.CABIN_TYPES.keys():
            cabins_left[type] = max(0, int(c.CABIN_TYPE_STOCKS[type]) - c.CABIN_TYPES_BOUGHT[type])
        return cabins_left
    
    @property
    def CABIN_TOTAL(self):
        running_total = 0
        for key, val in c.CABIN_TYPES_BOUGHT.items():
            running_total += val * int(c.CABIN_TYPE_PRICES[key])
        return running_total


c.CABIN_TYPE_OPTS = [(key, '{} (${})'.format(desc, int(c.CABIN_TYPE_PRICES[key])) if int(c.CABIN_TYPE_PRICES.get(key, 0)) else desc) for key, desc in c.CABIN_TYPE_OPTS]