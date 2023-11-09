import os
from datetime import date
from datetime import datetime as dt

from django.db import IntegrityError
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from contacts.models import Pendencies
from contacts.serializer import PendenciesSerializer
from control.functions import send_message
from control.models import MessageControl
from control.serializer import ControlMessageSerializer
from messages_api.models import Ticket
from webhook.utils.get_objects import get_digisac_contact_by_id
from webhook.utils.logger import Logger

# Create your views here.
logger = Logger(__name__)


class ControlMessageViewSet(viewsets.ModelViewSet):
    # queryset = MessageControl.objects.all()
    serializer_class = ControlMessageSerializer
    http_method_names = ["get", "post", "put", "patch"]

    def get_queryset(self):
        control_id = self.request.query_params.get("id")
        period = self.request.query_params.get("period")
        contact = self.request.query_params.get("contact")
        queryset = MessageControl.objects.all()

        if control_id:
            queryset = queryset.filter(control_id=control_id)
        if period and contact:
            queryset = queryset.filter(contact=contact, period=period)

        return queryset

    def create(self, request, *args, **kwargs):
        ticket_id = request.query_params.get("id")
        contact = request.query_params.get("phone")
        period = request.query_params.get("period")
        pendencies = request.query_params.get("pendencies")

        if not ticket_id:
            return Response(
                {"error": "You must provide a ticket id query parameters."}, status=400
            )
        if not pendencies:
            return Response(
                {"error": "You must provide a pendencies id query parameters."},
                status=400,
            )
        if not contact:
            return Response(
                {"error": "You must provide a contact id query parameters."}, status=400
            )

        try:
            ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
            control = MessageControl.objects.create(
                ticket=ticket, contact=contact, period=period
            )
        except (IntegrityError, TypeError) as e:
            error_code, error_msg = e.args
            text = str(error_msg)
            logger.debug(f"{text}")
            return Response(
                {f"error {error_code}": "Something Wrong", "message": text}, status=409
            )

        # obligation_control =
        serializer = ControlMessageSerializer(control)
        return Response(serializer.data, status=201)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())  # self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)

            if not queryset:
                return Response(
                    {"no_content": "There are no control of anyone ticket yet"},
                    status=200,
                )

            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=404)

    def up_control_message(self, request, control_message_id, retries):
        try:
            control_message = MessageControl.objects.get(id=control_message_id)
            if control_message:
                serializer = ControlMessageSerializer(control_message)
                serializer = ControlMessageSerializer(
                    control_message, data={"retries": retries}, partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {"success": 200, "data": serializer.data}, status=200
                    )

                return Response({"erro": serializer.errors}, status=400)
        except Exception as e:
            text = f"Update ticket: {control_message_id} failed"
            logger.debug(text)
            return Response(
                {"error": 500, "message": text, "cause": str(e)}, status=500
            )


@api_view(["PATCH"])
def update_control_message(request: HttpRequest):
    control_message_id = request.query_params.get("id")
    retries = request.query_params.get("retries")
    view = ControlMessageViewSet()
    # try:
    return view.up_control_message(request, control_message_id, retries)
    # except NotFoundException:
    #     return Response({'error': 400, 'message': "MessageControl não encontrado"}, status=400)
    # except Exception as e:
    #     return Response({'error': 400, 'message': str(e)}, status=400)


@api_view(["POST"])
def send_report_to_group(request: HttpRequest):
    text = request.data.get("text")
    group = request.query_params.get("group")

    if group is None:
        return Response(
            {
                "error": 400,
                "message": "Informe o grupo que vai receber a mensagem (?group='{group_name}')",
            },
            status=400,
        )

    send_message(
        os.environ.get(f"{group}_GROUP_ID", os.getenv(f"{group}_GROUP_ID")), text
    )
    return Response({"Success": f"Enviado para o grupo {group}"})


@api_view(["POST"])
def create_pendencies_viewset(request: HttpRequest):
    cnpj = request.query_params.get("cnpj")
    period_str = request.query_params.get("period")
    file = request.data.get("pdf")

    if cnpj is None or period_str is None:
        return Response(
            {"error": f"You must provide cnpj & period query params"}, status=400
        )

    if file is None:
        return Response(
            {"error": f"You must provide a base64 pdf converted on body fields 'pdf'"},
            status=400,
        )

    try:
        period = dt.strptime(period_str, "%Y-%m-%d").date()
    except ValueError:
        return Response(
            {"error": "Invalid date format. It should be YYYY-MM-DD."}, status=400
        )

    contact = get_digisac_contact_by_id(cnpj=cnpj)
    if contact is None:
        return Response({"error": f"No contact found with cnpj: {cnpj}"}, status=404)

    try:
        pendencie = Pendencies.objects.create(
            contact=contact,
            cnpj=cnpj,
            period=period,
            pdf=file,
        )
        serializer = PendenciesSerializer(pendencie)
        return Response(serializer.data, status=201)

    except (IntegrityError, TypeError) as e:
        text = str(e)
        logger.debug(f"{text}")
        return Response({f"error {e}": "Something Wrong", "message": text}, status=409)
