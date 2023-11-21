import os

from celery import shared_task
from django.db.utils import IntegrityError

from control.functions import check_client_response
from messages_api.views import get_valid_ticket
from webhook.exceptions import DigisacBugException
from webhook.functions.model_obj import (
    create_new_message,
    create_new_message_control,
    create_new_ticket,
)
from webhook.utils.get_objects import get_message, get_message_control, get_ticket
from webhook.utils.logger import Logger
from webhook.utils.tools import (
    IGNORED_ID_LISTS,
    DictAsObject,
    any_digisac_request,
    get_contact_number,
    get_current_period,
    get_event_status,
    message_exists_in_digisac,
    message_is_already_saved,
    update_ticket_last_message,
)

logger = Logger(__name__)


def load_env(var):
    return os.environ.get(var, os.getenv(var))


IS_LOCALHOST = load_env("IS_LOCALHOST")
WEBHOOK_API = load_env("WEBHOOK_API_LOCAL") if IS_LOCALHOST else load_env("WEBHOOK_API")


##-- Handler to events
# @shared_task(name="handler_task")
def manage(data):
    # Handlers de evento normalmente serão síncronos. Porém em casos específicos
    # alguns serão mandados para background.
    # Ex: quando um novo ticket é criado, ou uma mensagem é enviada
    event_handlers = {
        "message.created": (handle_message_created, ["id", "isFromMe"]),
        "message.updated": (handle_message_updated, ["id"]),
        "ticket.created": (handle_ticket_created, ["id", "contactId", "lastMessageId"]),
        "ticket.updated": (handle_ticket_updated, ["id"]),
    }
    # Aqui eu consigo filtrar os eventos que serão mandados para background
    event_will_apply_async = [
        handle_message_created,
        handle_ticket_created,
        handle_message_updated,
        handle_ticket_updated,
    ]
    #
    event = data.get("event")
    data = data.get("data")
    #
    event_handler_func, params = event_handlers.get(event, (None, []))
    #
    try:
        if (event == "message.created") and data.get("type") == "ticket":
            return f"Event: {event} has ticket type, avoiding to prevent message.created error"
    except AttributeError:
        return f"Event: {event} has some bug"
    #
    if event_handler_func:
        args = [data.get(param) for param in params]

        if any(
            [
                event_async == event_handler_func
                for event_async in event_will_apply_async
            ]
        ):
            event_handler_func.apply_async(args=args, kwargs={"data": data})

        # Setando qualquer outro evento normalmente como sincrono
        event_handler_func(*args, data=data)

    return f"Event: {event} handled to the function {event_handler_func.__name__}"


##-- Tasks to handle events
@shared_task(name="create_message")
def handle_message_created(message_id, isFromMe: bool, data=...):
    message_exists = message_exists_in_digisac(message_id=message_id)
    message_saved = message_is_already_saved(message_id=message_id)
    obs = ""
    #
    if message_exists and message_saved:
        # handle_message_updated(message_id, data=data)
        handle_message_updated.apply_async(args=[message_id], kwargs={"data": data})
        return "Mensagem já existe mandada pra atualização"
    #
    contact_id = data.get("contactId")
    date = get_current_period(dtObject=True)
    number = get_contact_number(contact_id=contact_id)
    message_data = {
        "contact_number": number,
        "period": date,
        "message_id": message_id,
        "contact_id": contact_id,
        "status": data["data"]["ack"],
        "ticket": data.get("ticketId"),
        "message_type": data.get("type"),
        "is_from_me": isFromMe,
        "text": data.get("text", data.get("type")),
    }
    #
    if not data.get("ticketId"):
        # return f"Ticket with ticket_id {data.get('ticketId')} not found."
        message_digisac = any_digisac_request(f"/messages/{message_id}", method="get")
        message_digisac = DictAsObject(message_digisac)
        obs += "ticket pego da API digisac"
        message_data["ticket"] = message_digisac.ticketId
    #
    if any(message_data.get("contact_id") == string for string in IGNORED_ID_LISTS):
        return "Ticket ignorado: Grupo de relatórios fiscais"
    #
    if number is None:
        raise ValueError(f"Consulta do telefone:{number} com id {contact_id} falhou")
    # if not isFromMe:
    # response = requests.post(url, json=message_body, params=parameters)

    try:
        message = create_new_message(**message_data)
    except IntegrityError as e:
        return f"Mensagem criada anteriormente. id:{message_id}"
    except DigisacBugException as e:
        return str(e)
    #
    if not isFromMe:
        check_client_response.apply_async(args=[contact_id])  # .get(contact_id)

    # Pega no digisac o id da ultima mensagem criada
    update_ticket_last_message.apply_async(args=[data.get("ticketId")])
    # except Exception as e:
    #     raise ObjectNotCreated(
    #         f"Failed to create message_id: {message_id} reason: \n{e}"
    #     )

    return f"Message Created successfully! OBS:({obs})"


@shared_task(name="update_message", queue="updates")
def handle_message_updated(message_id, data=...):
    if not message_id:
        return "Message vazio. diabo é isso?"

    message_exists = message_exists_in_digisac(message_id=message_id)
    message_saved = message_is_already_saved(message_id)

    # manda pra criação se a mensagem ainda não existir
    if message_exists and not message_saved:
        # REMOVE ASYNC DO EVENT HANDLER
        args = [message_id, data.get("isFromMe")]
        handle_message_created.apply_async(args=args, kwargs={"data": data})
        # handle_message_created(*args, data=data)
        return "Mensagem existe e não foi salva antes"

    try:
        data = data.get("data")
        message = get_message(message_id=message_id)
        actual_status = get_event_status("message", message_id=message_id)
        # O que está acontecendo aqui?? não entendi o isinstance de tupla
        status = data["ack"][0] if isinstance(data["ack"], tuple) else data.get("ack")
        if message:
            if actual_status < status:
                message.status = status
                message.save()
            else:
                return f"Status passado por parâmetro:{status} menor que o atualmente salva na mensagem com id: {message_id}"
        else:
            return f"Message with id {message_id} not found."

    except Exception as e:
        raise Exception(
            f"erro: {str(e)} - actual_status:{type(actual_status)} e status = {type(status)}"
        )

    return "Mensagem atualizada com sucesso"


@shared_task(name="create_ticket")
def handle_ticket_created(ticket_id, contact_id, last_message_id, data=...):
    # url = f"{WEBHOOK_API}/messages/create/ticket"
    ticket_data = {
        "id": ticket_id,
        "period": get_current_period(dtObject=True),
        "contact": contact_id,
        "last_message": last_message_id,
    }

    #
    if any(ticket_id == string for string in IGNORED_ID_LISTS):
        return "Ticket ignorado: Grupo de relatórios fiscais"

    # response = requests.post(url, params=params)
    # try:
    ticket, ticket_created = create_new_ticket(**ticket_data)
    contact = get_contact_number(contact_id=contact_id)

    message_control = get_message_control(
        digisac_id=contact_id,
        period=get_current_period(dtObject=True),
    )

    if not message_control:
        message_control = create_new_message_control(
            ticket=ticket,
            contact_number=contact,
            digisac_id=contact_id,
            period=get_current_period(dtObject=True),
        )

        return "ticket e message_control criados com sucesso"

    ticket_link = message_control.get_or_create_ticketlink()
    ticket_link.append_new_ticket(ticket)

    return "ticket adicionado com sucesso"

    # except Exception as e:
    # raise ObjectNotCreated(f"\nFailed to create ticket with id: {ticket_id}\n{e}")


@shared_task(name="update_ticket", queue="updates")
def handle_ticket_updated(ticket_id, data=...):
    actual_status = get_event_status("ticket", ticket_id=ticket_id)
    last_message_id = data.get("lastMessageId")
    is_open = data.get("isOpen")

    if actual_status and not is_open:
        ticket = get_valid_ticket(ticket_id=ticket_id)

        try:
            if ticket:
                ticket.is_open = is_open
                ticket.last_message_id = last_message_id
                ticket.save()

        except Exception as e:
            raise ValueError(str(e))

        return "Ticket atualizado com sucesso"
    else:
        return f"Ticket com id: {ticket_id} já está fechado ou ainda não foi criado"
