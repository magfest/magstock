from collections import defaultdict

from uber.config import c
from uber.decorators import cost_calculation, credit_calculation
from uber.receipt_items import Attendee


Attendee.cost_changes['brunch_tickets'] = ('Brunch Tickets ({} total)', "calc_meal_ticket_change", c.MEAL_TICKETS)
Attendee.cost_changes['dinner_tickets'] = ('Dinner Tickets ({} total)', "calc_meal_ticket_change", c.MEAL_TICKETS)
Attendee.cost_changes['camping_type'] = ('Camping Type ({})', "calc_camping_type_change", c.CAMPING_CABIN_TYPES)
Attendee.cost_changes['cabin_type'] = ('Camping Type ({})', "calc_camping_type_change", c.CAMPING_CABIN_TYPES)


@cost_calculation.Attendee
def brunch_tickets_cost(attendee):
    if attendee.brunch_tickets:
        return ("{} Brunch Ticket(s)".format(attendee.brunch_tickets), c.FOOD_PRICE * attendee.brunch_tickets * 100)


@cost_calculation.Attendee
def dinner_tickets_cost(attendee):
    if attendee.dinner_tickets:
        return ("{} Dinner Ticket(s)".format(attendee.dinner_tickets), c.FOOD_PRICE * attendee.dinner_tickets * 100)
    

@cost_calculation.Attendee
def camping_type_cost(attendee):
    if not attendee.camping_type:
        return
    if attendee.camping_type == c.CABIN:
        if not attendee.cabin_type:
            return
        return (attendee.cabin_type_label, int(c.CABIN_TYPE_PRICES[attendee.cabin_type]) * 100)
    return (attendee.camping_type_label, int(c.CAMPING_TYPE_PRICES[attendee.camping_type]) * 100)