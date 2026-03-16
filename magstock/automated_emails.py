from datetime import timedelta

from uber.automated_emails import AutomatedEmailFixture, MarketplaceEmailFixture, PanelAppEmailFixture
from uber.config import c
from uber.models import Attendee, AutomatedEmail
from uber.utils import before, days_before, days_after


AutomatedEmailFixture(
    Attendee, 'Thank you for your MAGStock Superstars Donation!',
    'superstar_intro.html',
    filter=lambda a: a.extra_donation >= c.SUPERSTAR_MINIMUM and a.active_receipt and not a.amount_unpaid,
    ident='superstar_intro',
    when=[before(c.SUPERSTAR_DEADLINE)],
    sender='MAGFest Superstar Program <superstars@magfest.org>'
)