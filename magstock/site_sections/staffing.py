import cherrypy
from datetime import datetime, timedelta
import ics
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from uber.config import c
from uber.custom_tags import safe_string
from uber.decorators import ajax, ajax_gettable, all_renderable, check_shutdown, csrf_protected, render, public
from uber.errors import HTTPRedirect
from uber.forms import load_forms
from uber.models import Attendee, Job, FoodRestrictions
from uber.utils import check_csrf, create_valid_user_supplied_redirect_url, ensure_csrf_token_exists, localized_now, extract_urls, validate_model

@all_renderable()
class Root:
    @check_shutdown
    def hotel(self, session, message='', decline=None, **params):
        if c.AFTER_ROOM_DEADLINE and not c.HAS_STAFFING_ADMIN_ACCESS:
            raise HTTPRedirect('../staffing/index?message={}', 'The bed request deadline has passed.')
        attendee = session.logged_in_volunteer()
        if not attendee.hotel_eligible:
            raise HTTPRedirect('../staffing/index?message={}', 'You have not been marked as eligible for bed space.')
        
        requests = attendee.hotel_requests
        if cherrypy.request.method == "POST":
            requests = requests
            session.add(requests)
            if decline:
                requests.nights = ''
                raise HTTPRedirect(
                    '../staffing/index?message={}', "We've recorded that you've declined bed space.")
            else:
                requests.nights = ','.join(map(str, c.CORE_NIGHTS))
                raise HTTPRedirect('../staffing/index?message={}', "Thanks for letting us know that you've filled out the bed request form!")
        return {
            'message':  message,
            'requests': requests,
            'attendee': attendee
        }