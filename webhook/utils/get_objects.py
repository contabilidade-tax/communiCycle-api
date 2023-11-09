import os
import time
from typing import Union

import httpx
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404

from control.models import DASFileGrouping, MessageControl, TicketLink
from messages_api.models import Message, Ticket
from webhook.exceptions import ContactNotFound, ObjectNotFound

max_retries = 5
att_tax = 0.1
COMPANIES_API = settings.COMPANIES_API


def get_company_contact_by_cnpj(cnpj: Union[str, int], **kwargs):
    request = httpx.get(f"{COMPANIES_API}/contacts/{cnpj}")

    if request.status_code == 200:
        return request.json()
        # return DictAsObject(request.json())

    raise ContactNotFound(f"Contact for {cnpj} not found")


def get_digisac_contact_by_id(contact_id: str, **kwargs):
    request = httpx.get(f"{COMPANIES_API}/contacts/digisac/{contact_id}")

    if request.status_code == 200:
        return request.json()
        # return DictAsObject(request.json())

    raise ContactNotFound(f"Contact for id:{contact_id} not found")


def get_all_contact_by_digisac_id(digisac_id: str, **kwargs):
    request = httpx.get(f"{COMPANIES_API}/contacts/digisac/all/{digisac_id}")

    if request.status_code == 200:
        return request.json()
        # return DictAsObject(request.json())

    raise ContactNotFound(f"Anyone contact for id:{digisac_id} not found")


def get_message_control(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            control = get_object_or_404(MessageControl, **kwargs)
            return control
        except Http404:
            time.sleep(att_tax)
            retries += 1
    return None


def get_ticket_link(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            ticket_link = get_object_or_404(TicketLink, **kwargs)
            return ticket_link
        except Http404:
            time.sleep(att_tax)
            retries += 1
    return None


def get_message(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            message = get_object_or_404(Message, **kwargs)
            return message
        except Http404:
            time.sleep(att_tax)
            retries += 1

    return None
    # raise ObjectNotFound(f"Anyone message for {kwargs.get('message_id')} not found")


def get_valid_ticket(ticket_id):
    while True:
        try:
            ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
            return ticket
        except Http404:
            time.sleep(0.5)


def get_ticket(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            ticket = get_object_or_404(Ticket, **kwargs)
            return ticket
        except Http404:
            time.sleep(att_tax)
            retries += 1
    return None


def get_das_grouping(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            grouping = get_object_or_404(DASFileGrouping, **kwargs)
            return grouping
        except Http404:
            time.sleep(att_tax)
            retries += 1
    return None
