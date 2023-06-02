from collections import defaultdict
from sqlalchemy import func, or_

from uber.config import c
from uber.decorators import ajax, all_renderable, csv_file
from uber.models import Attendee


def camp_food_report(session):
    attendees_with_meal_tickets = sorted(session.attendees_with_badges().filter(
        or_(Attendee.brunch_tickets > 0, Attendee.dinner_tickets > 0)), key=lambda a: a.full_name)
    brunch_data = defaultdict(int)
    dinner_data = defaultdict(int)
    total_data = defaultdict(int)

    total_data['attendees'] = []

    for attendee in attendees_with_meal_tickets:
        total_data['attendees'].append(attendee)
        total_data['attendee_count'] += 1

        if attendee.brunch_tickets:
            brunch_data['attendee_count'] += 1
            brunch_data['ticket_count'] += attendee.brunch_tickets
            for restriction in attendee.meal_restrictions:
                brunch_data[restriction] += 1

        if attendee.dinner_tickets:
            dinner_data['attendee_count'] += 1
            dinner_data['ticket_count'] += attendee.dinner_tickets
            for restriction in attendee.meal_restrictions:
                dinner_data[restriction] += 1
        
        for restriction in attendee.meal_restrictions:
            total_data[restriction] += 1
            brunch_data[restriction] += bool(attendee.brunch_tickets > 0)
            dinner_data[restriction] += bool(attendee.dinner_tickets > 0)

    return brunch_data, dinner_data, total_data

@all_renderable()
class Root:
    def grouped(self, session, noise=None, site=None, camp=None):
        attendees = session.query(Attendee).all()

        names = {}
        for attendee in attendees:
            names.setdefault(attendee.last_name.lower(), set()).add(attendee)

        lookup = defaultdict(set)
        for xs in names.values():
            for attendee in xs:
                lookup[attendee] = xs

        def match(a):
            return (not camp or a.camping_type == int(camp))

        def any_match(group):
            return any(match(a) for a in group)

        return {
            'camp': camp,
            'site': site,
            'noise': noise,
            'grouped': sorted(
                {frozenset(group) for group in lookup.values() if any_match(group)}, key=len, reverse=True)
        }

    def food_consumers(self, session):
        brunch_data, dinner_data, total_data = camp_food_report(session)
        return {
            'brunch_data': brunch_data,
            'dinner_data': dinner_data,
            'total_data': total_data,
        }
    
    @csv_file
    def food_consumers_report(self, out, session):
        brunch_data, dinner_data, total_data = camp_food_report(session)
        header_row = [
            '# Attendees',
            'Brunch Tickets',
            'Dinner Tickets',
            'Total Tickets',
        ]

        data_row = [
            total_data['attendee_count'],
            brunch_data['ticket_count'],
            dinner_data['ticket_count'],
            brunch_data['ticket_count'] + dinner_data['ticket_count']
            ]

        for restriction, label in c.MEAL_TICKET_RESTRICTION_OPTS:
            header_row.append(label)
            data_row.append(total_data[restriction])

        out.writerow(header_row)
        out.writerow(data_row)

    def parking(self, session):
        """
        This report shows all cars parked in places
        """

        return {
            'attendees': session.query(Attendee).filter().all()
        }

    @ajax
    def set_extra_checkin_fields(self, session, id, license_plate):
        attendee = session.attendee(id)
        attendee.license_plate = license_plate
        session.commit()
        return {'message': 'success'}
    
    def addons(self, session):
        return {
            'all_cabins_stock': sum([int(val) for key, val in c.CABIN_TYPE_STOCKS.items()]),
            'brunch_ticket_count': session.valid_attendees().with_entities(func.sum(Attendee.brunch_tickets)).scalar(),
            'dinner_ticket_count': session.valid_attendees().with_entities(func.sum(Attendee.dinner_tickets)).scalar(),
        }
