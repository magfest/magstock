from collections import defaultdict

from uber.config import c
from uber.decorators import receipt_calculation
from uber.receipt_items import Attendee


@receipt_calculation.Attendee
def meal_plan_cost(attendee, new_attendee=None):
    if not new_attendee and attendee.meal_plan == c.NO_FOOD:
        return
    elif not new_attendee:
        return ("Add Meal Plan", int(c.MEAL_PLAN_PRICES[attendee.meal_plan]) * 100, 'meal_plan')
    
    old_cost = int(c.MEAL_PLAN_PRICES[attendee.meal_plan]) * 100
    new_cost = int(c.MEAL_PLAN_PRICES[new_attendee.meal_plan]) * 100

    if old_cost == new_cost:
        return

    if attendee.meal_plan == c.NO_FOOD:
        return ("Add Meal Plan", new_cost, 'meal_plan')
    elif new_attendee.meal_plan == c.NO_FOOD:
        return ("Remove Meal Plan", old_cost * -1, 'meal_plan')
    else:
        prefix = "Upgrade" if new_cost > old_cost else "Downgrade"
        return (f"{prefix} Meal Plan", new_cost - old_cost, 'meal_plan')


@receipt_calculation.Attendee
def camping_type_cost(attendee, new_attendee=None):
    if not new_attendee:
        if attendee.camping_type == c.CABIN or not int(c.CAMPING_TYPE_PRICES[attendee.camping_type]) * 100:
            return
        return (f"Add {attendee.camping_type_label} Camping",
                int(c.CAMPING_TYPE_PRICES[attendee.camping_type]) * 100, 'camping_type')
        
    if attendee.camping_type == c.CABIN or new_attendee.camping_type == c.CABIN:
        return
    
    old_cost = int(c.CAMPING_TYPE_PRICES[attendee.camping_type]) * 100
    new_cost = int(c.CAMPING_TYPE_PRICES[new_attendee.camping_type]) * 100

    if old_cost == new_cost:
        return

    prefix = "Upgrade" if new_cost > old_cost else "Downgrade"

    return (f"{prefix} to {new_attendee.camping_type_label} Camping", new_cost - old_cost, 'camping_type')


@receipt_calculation.Attendee
def cabin_type_cost(attendee, new_attendee=None):
    if not new_attendee:
        if not attendee.cabin_type or attendee.camping_type != c.CABIN:
            return
        return (f"Add {attendee.cabin_type_label}",
            int(c.CABIN_TYPE_PRICES[attendee.cabin_type]) * 100, ('camping_type', 'cabin_type'))

    old_cost = (int(c.CABIN_TYPE_PRICES[attendee.cabin_type]) * 100) if attendee.cabin_type else None
    new_cost = (int(c.CABIN_TYPE_PRICES[new_attendee.cabin_type]) * 100) if new_attendee.cabin_type else None
    
    if attendee.camping_type != c.CABIN and new_attendee.camping_type != c.CABIN:
        return
    elif attendee.camping_type != c.CABIN:
        if not new_attendee.cabin_type:
            return
        old_cost = int(c.CAMPING_TYPE_PRICES[attendee.camping_type]) * 100
        label = f"Upgrade to {new_attendee.cabin_type_label}"
    elif new_attendee.camping_type != c.CABIN:
        if not attendee.cabin_type:
            return
        new_cost = int(c.CAMPING_TYPE_PRICES[new_attendee.camping_type]) * 100
        label = f"Downgrade to {new_attendee.camping_type_label} Camping"
    elif old_cost is not None and new_cost is not None:
        label = "Upgrade" if new_cost > old_cost else "Downgrade"
        label += f" to {new_attendee.cabin_type_label}"

    if old_cost == new_cost or old_cost is None or new_cost is None:
        return
    
    return (label, new_cost - old_cost, ('camping_type', 'cabin_type'))


Attendee.receipt_changes['meal_plan'] = (meal_plan_cost, None)
Attendee.receipt_changes['camping_type'] = (camping_type_cost, None)
Attendee.receipt_changes['cabin_type'] = (cabin_type_cost, None)