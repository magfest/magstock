from collections import defaultdict

from uber.config import c
from uber.decorators import cost_calculation, credit_calculation
from uber.receipt_items import Attendee


Attendee.cost_changes['meal_plan'] = ('Meal Plan ({})', "calc_meal_plan_change", c.MEAL_PLANS)
Attendee.cost_changes['camping_type'] = ('Camping Type ({})', "calc_camping_type_change", c.CAMPING_CABIN_TYPES)
Attendee.cost_changes['cabin_type'] = ('Camping Type ({})', "calc_camping_type_change", c.CAMPING_CABIN_TYPES)


@cost_calculation.Attendee
def meal_plan_cost(attendee):
    return (attendee.meal_plan_label, int(c.MEAL_PLAN_PRICES[attendee.meal_plan]) * 100, 'meal_plan')
    

@cost_calculation.Attendee
def camping_type_cost(attendee):
    if not attendee.camping_type:
        return
    if attendee.camping_type == c.CABIN:
        if not attendee.cabin_type:
            return
        return (attendee.cabin_type_label, int(c.CABIN_TYPE_PRICES[attendee.cabin_type]) * 100, 'cabin_type')
    return (attendee.camping_type_label, int(c.CAMPING_TYPE_PRICES[attendee.camping_type]) * 100, 'camping_type')
