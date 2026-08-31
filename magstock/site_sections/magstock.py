from collections import defaultdict
from sqlalchemy import func, or_

from uber.config import c
from uber.custom_tags import datetime_local_filter
from uber.decorators import ajax, all_renderable, csv_file
from uber.models import Attendee, ReceiptItem, ModelReceipt


def camp_food_report(session):
    attendees_with_meal_plan = sorted(session.valid_attendees().filter(
        Attendee.meal_plan != c.NO_FOOD), key=lambda a: a.full_name)
    total_data = defaultdict(int)

    total_data['attendees'] = []
    total_data['owe_money'] = {}

    for attendee in attendees_with_meal_plan:
        total_data['attendees'].append(attendee)
        total_data['attendee_count'] += 1

        if attendee.amount_unpaid:
            total_data['owe_money'][attendee.id] =  attendee.amount_unpaid

        if attendee.meal_plan == c.BEVERAGE:
            total_data['beverage'] += 1
        elif attendee.meal_plan == c.FULL_FOOD:
            total_data['full_food'] += 1

            for restriction in attendee.meal_restrictions_ints:
                total_data[restriction] += 1

    return total_data

def camp_cabin_report(session):
    attendees_with_cabins = session.valid_attendees().filter(Attendee.camping_type == c.CABIN)
    total_data = defaultdict(int)
    
    total_data['attendees'] = sorted(attendees_with_cabins.all(), key=lambda a: a.full_name)
    total_data['attendee_count'] = attendees_with_cabins.count()
    total_data['owe_money'] = {}

    for attendee in [a for a in attendees_with_cabins if a.amount_unpaid]:
        total_data['owe_money'][attendee.id] = attendee.amount_unpaid

    for cabin_type in c.CABIN_TYPES.keys():
        total_data[cabin_type] = attendees_with_cabins.filter(Attendee.cabin_type == cabin_type).count()
        total_data['type_total'] += total_data[cabin_type]
    
    total_data['discrepancy_count'] = total_data['attendee_count'] - total_data['type_total']
    
    return total_data

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
    
    @csv_file
    def staff_hats_report(self, out, session):
        out.writerow([
            'Name',
            'Email',
            'Needs hat?'
        ])
        for staff in session.query(Attendee).filter(Attendee.is_valid == True, Attendee.badge_type == c.STAFF_BADGE):
            out.writerow([
                staff.full_name,
                staff.email,
                staff.staff_hat_label
            ])

    def food_consumers(self, session):
        total_data = camp_food_report(session)
        return {
            'total_data': total_data,
        }
    
    @csv_file
    def food_consumers_report(self, out, session):
        total_data = camp_food_report(session)
        header_row = [
            '# Attendees',
            '# Beverage Plans'
            '# Full Meal Plans',
        ]

        data_row = [
            total_data['attendee_count'],
            total_data['beverage'],
            total_data['full_food'],
            ]

        for restriction, label in c.MEAL_TICKET_RESTRICTION_OPTS:
            header_row.append(label)
            data_row.append(total_data[restriction])

        out.writerow(header_row)
        out.writerow(data_row)
    
    def cabin_purchasers(self, session):
        total_data = camp_cabin_report(session)
        return {
            'total_data': total_data,
        }
    
    @csv_file
    def cabin_purchasers_report(self, out, session):
        total_data = camp_cabin_report(session)
        header_row = [
            '# Attendees',
        ]

        data_row = [
            total_data['attendee_count'],
            ]

        for type, label in c.CABIN_TYPE_OPTS:
            header_row.append(label)
            data_row.append(total_data[type])

        if total_data['discrepancy_count']:
            header_row.append("Attendees With Null Cabins")
            data_row.append(total_data['discrepancy_count'])

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
            'beverage_plan_count': session.valid_attendees().filter(Attendee.meal_plan == c.BEVERAGE).count(),
            'full_plan_count': session.valid_attendees().filter(Attendee.meal_plan == c.FULL_FOOD).count(),
        }
    
    def superstars(self, session):
        counts = {}
        owe_money = {}
        superstars = session.valid_attendees().filter(Attendee.extra_donation >= c.SUPERSTAR_MINIMUM)

        valid_donations_list = c.SUPERSTAR_DONATION_OPTS[1:-1]
        last_index = len(valid_donations_list) - 1
        for index, opt in enumerate(valid_donations_list):
            amt, label = opt
            count_query = session.valid_attendees().filter(Attendee.extra_donation >= amt)
            if index != last_index:
                next_amt, next_label = valid_donations_list[index + 1]
                count_query = count_query.filter(Attendee.extra_donation < next_amt)
            counts[label] = count_query.count()

        for attendee in [a for a in superstars if a.amount_unpaid or not a.active_receipt]:
            owe_money[attendee.id] = attendee.amount_unpaid if attendee.active_receipt else attendee.default_cost
        
        return {
            'attendees': superstars,
            'counts': counts,
            'owe_money': owe_money,
            'total_count': superstars.count(),
        }
    
    @csv_file
    def superstars_csv(self, out, session):
        out.writerow(["Group Name", "Full Name", "Name on ID", "Badge Type", "Ribbons", "Pre-ordered Merch",
                      "Donation", "Email", "ZIP/Postal Code", "Checked In"])
        for a in session.valid_attendees().filter(Attendee.extra_donation >= c.SUPERSTAR_MINIMUM):
            out.writerow([a.group_name, a.full_name, a.legal_name, a.badge_type_label,
                          ' / '.join(a.ribbon_labels), a.amount_extra_label, a.extra_donation, a.email, a.zip_code,
                          datetime_local_filter(a.checked_in)])
            
    @csv_file
    def superstar_donations_by_date_csv(self, out, session):
        out.writerow(["URL", "Full Name", "Email", "Donation Amount", "Donation Date", "Current Total Donation"])
        extra_donations = session.query(ReceiptItem, Attendee.id, Attendee.first_name,
                                        Attendee.last_name, Attendee.email, Attendee.extra_donation,
                                        ).join(ModelReceipt).join(Attendee, Attendee.id == ModelReceipt.owner_id).filter(
            ModelReceipt.owner_model == "Attendee", ReceiptItem.desc.contains("Extra Donation"),
            ReceiptItem.closed != None, ReceiptItem.amount > 0).order_by(ReceiptItem.closed)
        for donation, id, first_name, last_name, email, total_donation in extra_donations:
            url = "{}/registration/form?id={}".format(c.URL_BASE, id)
            out.writerow([url, f"{first_name} {last_name}", email, (donation.total_amount / 100),
                          datetime_local_filter(donation.closed), total_donation])
