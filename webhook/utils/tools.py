import enum
import os
import socket
from datetime import datetime as dt
from datetime import timedelta
from typing import Union

from celery import shared_task
from dotenv import load_dotenv
from httpx import Client, get

from webhook.utils.get_objects import get_digisac_contact_by_id, get_message, get_ticket
from webhook.utils.logger import Logger

load_dotenv()


logger = Logger(__name__)

IGNORED_ID_LISTS = ["4bf3c03a-2d33-439c-8b13-efb50531e9c1"]


class request_methods(enum.Enum):
    get = "get"
    post = "post"


def get_digisac_ticket(ticket_id):
    response = any_digisac_request(f"/tickets/{ticket_id}", method="get", json=False)

    if response.status_code == 200:
        response_dict = {}
        ticket = response_dict.json()

        response_dict["ticket_id"] = ticket_id
        response_dict["period"] = get_current_period(dtObject=True)
        response_dict["contact_id"] = ticket["contactId"]
        response_dict["last_message_id"] = ticket["lastMessageId"]


##-- Digisac requests
def any_digisac_request(
    url, body=None, method: Union[request_methods, str] = request_methods.get, json=True
):
    header = {
        "Authorization": f"Bearer {os.environ.get('TOKEN_DIGISAC_API', os.getenv('TOKEN_DIGISAC_API'))}",
        "Content-Type": "application/json",
    }

    with Client(
        base_url=os.environ.get("DIGISAC_API_URL", os.getenv("DIGISAC_API_URL")),
        headers=header,
    ) as client:
        if method == "get":
            get_response: get = client.get(url, timeout=6000)
            return get_response.json() if json else get_response
        if method == "post":
            response = client.post(url, json=body, timeout=6000)
            if response.status_code == 200:
                return response.json() if json else response
            else:
                raise ValueError(f"Something wrong - {response} - {response.json()}")


def get_chat_protocol(ticketId):
    try:
        header = {
            "Authorization": f"Bearer {os.environ.get('TOKEN_DIGISAC_API', os.getenv('TOKEN_DIGISAC_API'))}",
            "Content-Type": "application/json",
        }

        with Client(
            base_url=os.environ.get("DIGISAC_API_URL", os.getenv("DIGISAC_API_URL"))
        ) as client:
            response = client.get(f"/tickets/{ticketId}", headers=header)

            if response.status_code == 200:
                data = response.json()
                return data["protocol"]
    except Exception as e:
        logger.error(f"Exception occurred: \n{e}")


##--Contact utils
def get_contact_number(contact_id: str, only_number=False):
    contact = get_digisac_contact_by_id(contact_id=contact_id)
    contact = DictAsObject(contact)

    if contact:
        if not only_number:
            return f"{contact.country_code}{contact.ddd}{contact.contact_number}"
        else:
            return f"{contact.contact_number}"

    return None


def get_current_period(file_name=False, dtime=False, dtObject=False) -> str:
    if file_name:
        return (
            (dt.today().replace(day=1) - timedelta(days=1))
            .strftime("%B/%Y")
            .capitalize()
        )

    if dtime:
        return dt.today()

    if dtObject:
        return dt.now().date().strftime("%Y-%m-%d")

    return dt.today().strftime("%m/%y")


saudacao = f"""Olá, espero que esteja bem.
Gostaria de informar que seu Documento de Arrecadação Simplificado(DAS) 
período ({get_current_period(file_name=True)}) está disponível, irei envia-lo em seguida.
Lembrando que é importante que o pagamento seja realizado
dentro do prazo estipulado para evitar juros e multa
"""
suggest = "Qualquer dúvida ou sugestão entre em contato através do WhatsApp: https://wa.me/5588988412833."
disclaimer = f"""
{suggest}

Por favor, preciso que confirme o recebimento desta mensagem. 
Responda SIM, OK, ou RECEBI por gentileza.
"""


##-- Additional functions
def get_event_status(event, message_id: str = None, ticket_id: str = None):
    if event == "ticket":
        ticket = get_ticket(ticket_id=ticket_id)
        return ticket.is_open if ticket else False

    if event == "message":
        message = get_message(message_id=message_id)
        return message.status if message else 0


@shared_task(name="update_ticket_last_message")
def update_ticket_last_message(ticket_id: str):
    response = any_digisac_request(f"/tickets/{ticket_id}", method="get", json=False)

    if response.status_code == 200:
        try:
            digisac_ticket = response.json()
            last_message_id = digisac_ticket.get("lastMessageId")
            is_open = digisac_ticket.get("isOpen")

            ticket = get_ticket(ticket_id=ticket_id)
            ticket.last_message_id = last_message_id
            ticket.is_open = is_open
            ticket.save()

            return "Show Papai. Atualizado!!"
        except Exception as e:
            raise ValueError(f"Algo de errado não está certo - {e}")

    return "Nada foi feito! Ticket provavelmente ainda não foi criado"


def message_exists_in_digisac(message_id):
    message = any_digisac_request(f"/messages/{message_id}", method="get", json=True)

    if message["sent"]:
        return True
    else:
        return False


def message_is_already_saved(message_id) -> bool:
    # Esse método retorna None se não encontrar o objeto, logo num if qualquer resposta
    # não deverá ter problema
    message = get_message(message_id=message_id)

    return True if message else False


def group_das_to_send(contact_id: str, companie: str, period):
    from control.models import DASFileGrouping

    grouping, created = DASFileGrouping.objects.get_or_create(
        contact_id=contact_id, period=period
    )

    grouping.append_new_companie(companie)
    return grouping


class DictAsObject:
    def __init__(self, dictionary):
        for key in dictionary:
            # Aqui garantimos que somente as chaves existentes no dicionário sejam atribuídas
            setattr(self, key, dictionary[key])
