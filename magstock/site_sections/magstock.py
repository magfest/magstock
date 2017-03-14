from uber.common import *
from sqlalchemy.sql.expression import cast


@all_renderable(c.PEOPLE)
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

        for attendee in attendees:
            for word in attendee.coming_with.lower().replace(',', ' ').split():
                try:
                    combined = lookup[list(names[word])[0]] | lookup[attendee]
                    for attendee in combined:
                        lookup[attendee] = combined
                except:
                    pass

        def match(a):
            return ((not site or a.site_type == int(site))
                and (not camp or a.camping_type == int(camp))
                and (not noise or a.noise_level == int(noise)))

        def any_match(group):
            return any(match(a) for a in group)

        return {
            'camp': camp,
            'site': site,
            'noise': noise,
            'grouped': sorted({frozenset(group) for group in lookup.values() if any_match(group)}, key=len, reverse=True)
        }

    def food_consumers(self, session):
        attendees = sorted(session.food_consumers(), key=lambda a: a.full_name)
        paid_food_count = len([a for a in attendees if a.purchased_food])
        free_food_count = len(attendees) - paid_food_count
        return {
            'attendees': attendees,
            'paid_food_count': paid_food_count,
            'free_food_count': free_food_count,
        }

    def campsite_assignments(self, session):
        """
        This report shows all campsites and who is in them (or no one)
        """

        campsite_assignments = []
        for site_id, site_name in c.CAMPSITE_OPTS:
            campsite_assignments.append({'site_name': site_name, 'attendees':
                session.query(Attendee).filter(cast(site_id, sqlalchemy.String) == Attendee.site_number).all()})

        return {
            'campsite_assignments': campsite_assignments
        }

    def parking(self, session):
        """
        This report shows all cars parked in places
        """

        return {
            'attendees': session.query(Attendee).filter().all()
        }

    @ajax
    def set_extra_checkin_fields(self, session, id, site_number, license_plate):
        attendee = session.attendee(id)
        attendee.site_number = site_number
        attendee.license_plate = license_plate
        session.commit()
        return {'message': 'success'}
