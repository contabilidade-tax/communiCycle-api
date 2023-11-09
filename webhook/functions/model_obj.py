from django.conf import settings

from control.models import Message, MessageControl, Ticket
from webhook.exceptions import ObjectNotFound
from webhook.utils.get_objects import get_ticket
from webhook.utils.tools import DictAsObject


def check_has_value(anything, error_message=""):
    if anything:
        return True

    raise ObjectNotFound(
        f"Object of {type(anything)} not valid or not found"
        if not error_message
        else error_message
    )


def create_new_message(**kwargs) -> Message:
    data = DictAsObject(kwargs)
    #
    contact_number = data.contact_number
    period = data.period
    message_id = data.message_id
    contact_id = data.contact_id
    status = data.status
    ticket_id = data.ticket
    message_type = data.message_type
    isFromMe = data.is_from_me
    text = data.text
    #
    ticket = get_ticket(ticket_id=ticket_id)
    #

    if not contact_id in settings.IGNORED_ID_LISTS:
        check_has_value(ticket, f"Ticket not found: {ticket_id}")

    message, created = Message.objects.get_or_create(
        message_id=message_id,
        contact_id=contact_id,
        contact_number=contact_number,
        period=period,
        status=status,
        ticket=ticket,
        message_type=message_type,
        is_from_me=isFromMe,
        text=text,
        retries=0,
    )
    return message


def create_new_ticket(**kwargs) -> Ticket:
    data = DictAsObject(kwargs)
    ticket_id = data.id
    period = data.period
    contact_id = data.contact
    last_message_id = data.last_message
    #
    ticket, created = Ticket.objects.get_or_create(
        ticket_id=ticket_id,
        period=period,
        contact_id=contact_id,
        last_message_id=last_message_id,
    )
    #
    return ticket, created


def create_new_message_control(ticket: Ticket, **kwargs) -> MessageControl:
    data = DictAsObject(kwargs)
    #
    ticket = ticket
    contact_number = data.contact_number
    digisac_id = data.digisac_id
    period = data.period
    #
    message_control, created = MessageControl.objects.get_or_create(
        ticket=ticket,
        contact_number=contact_number,
        digisac_id=digisac_id,
        period=period,
    )
    #
    return message_control, created
