from os.path import join
from pathlib import Path

from uber.config import c, Config, dynamic, parse_config, request_cached_property
from uber.menu import MenuItem
from uber.models import Attendee, Session

from magstock._version import __version__  # noqa: F401

config = parse_config("magstock", Path(__file__).parents[0])
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
            {'name': 'Tent', 'icon': '', 'link': '', 'value': c.TENT, 'price': c.CAMPING_TYPE_PRICES[c.TENT],
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
    def FORMATTED_MEAL_PLANS(self):
        return [
            {'name': 'No thanks', 'icon': '', 'link': '', 'value': c.NO_FOOD,
             'price': c.MEAL_PLAN_PRICES[c.NO_FOOD], 'desc': 'No food or beverage mess hall access.'},
            {'name': 'Beverage Plan', 'icon': '', 'link': '', 'value': c.BEVERAGE,
             'price': c.MEAL_PLAN_PRICES[c.BEVERAGE], 'desc': 'Full event mess hall beverage access.'},
            {'name': 'Full Meal Plan', 'icon': '', 'link': '', 'value': c.FULL_FOOD,
             'price': c.MEAL_PLAN_PRICES[c.FULL_FOOD],
             'desc': 'Includes 6 meals (Dinner THU, Brunch and Dinner FRI+SAT, Brunch SUN) '
             'AND full event mess hall beverage access.'},
        ]

    @property
    def CAMPING_CABIN_TYPES(self):
        # For use with camping and cabin-related cost changes
        return {**c.CAMPING_TYPES, **c.CABIN_TYPES}

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