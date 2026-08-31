from collections.abc import Mapping
from datetime import timedelta, datetime
import pytz
from time import sleep, time
import traceback

from celery.schedules import crontab
from sqlalchemy.orm import joinedload

from uber import utils
from uber.amazon_ses import email_sender
from uber.automated_emails import AutomatedEmailFixture
from uber.config import c
from uber.decorators import render
from uber.email import EmailService
from uber.models import AutomatedEmail, Email, MagModel, Attendee, Session, ReceiptItem, ModelReceipt
from uber.tasks import celery


@celery.schedule(crontab(minute=0, hour=0))
def superstar_receipts():
    with Session() as session:
        extra_donations = session.query(ReceiptItem).join(ModelReceipt).filter(
            ReceiptItem.desc.contains("Extra Donation"), ReceiptItem.closed != None, ReceiptItem.amount > 0,
            ModelReceipt.owner_model == "Attendee")
        for donation in extra_donations:
            attendee = session.query(Attendee).filter(Attendee.id == donation.receipt.owner_id).first()
            if not attendee.amount_unpaid:
                closed_local = donation.closed.astimezone(c.EVENT_TIMEZONE).strftime('%x_%X')
                ident = f'superstar_receipt_{int(donation.amount / 100)}_{closed_local}'
                already_emailed = session.query(Email.ident).filter(Email.ident == ident,
                                                                    Email.fk_id == attendee.id).first()
                if not already_emailed:
                    EmailService.queue_email(session, 'superstar_receipt', attendee,
                                             subject=f"MAGStock {c.EVENT_YEAR} Superstar Donation Receipt",
                                             data={'donation': donation})