from datetime import datetime as dt

from django.db import IntegrityError
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from contacts.models import CompanyContact, Contact
from contacts.serializer import CompanyContactSerializer
from webhook.utils.get_objects import get_digisac_contact_by_id
from webhook.utils.logger import Logger

# Create your views here.

logger = Logger(__name__)


# Company Contact
class ContactViewSet(viewsets.ModelViewSet):
    # queryset = Contact.objects.all()
    serializer_class = CompanyContactSerializer
    http_method_names = ["get", "post", "put", "patch"]

    def get_queryset(self):
        contact_id = self.request.query_params.get("id")
        cnpj = self.request.query_params.get("cnpj")
        contact = self.request.query_params.get("contact")
        queryset = CompanyContact.objects.all()

        if cnpj:
            queryset = queryset.filter(cnpj=cnpj)
        if contact:
            queryset = queryset.filter(contact_number=contact)
        if contact_id:
            queryset = queryset.filter(contact_id=contact_id)

        return queryset

    def create(self, request, *args, **kwargs):
        cnpj = request.query_params.get("cnpj")
        contact_id = request.query_params.get("id")
        company_name = request.data.get("company_name")
        responsible_name = request.data.get("responsible_name")
        establishment_id = request.data.get("establishment_id")
        country_code = request.data.get("country_code")
        ddd = request.data.get("ddd")
        contact_number = request.data.get("contact_number")

        if not cnpj:
            return Response(
                {"error": "You must provide a CNPJ query parameter."}, status=400
            )
        if not contact_id:
            return Response(
                {"error": "You must provide a CONTACT_ID id query parameter."},
                status=400,
            )

        try:
            company_contact = get_digisac_contact_by_id(
                cnpj=cnpj, establishment_id=establishment_id
            )

            if not company_contact:
                company_contact = CompanyContact.objects.create(
                    cnpj=cnpj,
                    company_name=company_name,
                    establishment_id=establishment_id,
                    responsible_name=responsible_name,
                )
            else:
                raise IntegrityError(
                    "Opaaa, já tem um company_contact com esses dados major"
                )

            contact = company_contact.get_or_create_contact(
                contact_id=contact_id,
                country_code=country_code,
                ddd=ddd,
                contact_number=contact_number,
            )

            if contact:
                contact.append_new_contact(company_contact)
                contact.append_new_establishment(establishment_id)

            serializer = CompanyContactSerializer(company_contact)
            return Response(serializer.data, status=201)
        except (IntegrityError, TypeError) as e:
            text = str(e)
            logger.debug(f"{text}")
            return Response({f"error": "Something Wrong", "message": text}, status=409)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())  # self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)

            if not queryset:
                return Response(
                    {"no_content": "There are no yet contacts to show"}, status=200
                )

            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=404)

    def up_ticket(self, request, contact_id, is_open):
        try:
            contact = Contact.objects.get(contact_id=contact_id)
            if contact:
                serializer = CompanyContactSerializer(contact)
                serializer = CompanyContactSerializer(
                    contact, data={"is_open": is_open}, partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {"success": 200, "data": serializer.data}, status=200
                    )

                return Response({"erro": serializer.errors}, status=400)
        except Exception as e:
            text = f"Update Contact: {contact_id} failed"
            logger.debug(text)
            return Response(
                {"error": 500, "message": text, "cause": str(e)}, status=500
            )


@api_view(["PATCH"])
def update_contact(request):
    cnpj = request.query_params.get("cnpj")
    name = request.query_params.get("name")
    company_contact = get_digisac_contact_by_id(cnpj=cnpj)

    if not (cnpj or name):
        return Response("CNPJ & name must be present in update request", status=400)

    try:
        contact = company_contact.contact
        contact.name = name
        contact.save()

        company_contact.save()
    except Exception as e:
        return Response({"error": {"code": 500, "message": str(e)}}, status=500)

    return Response("Contato atualizado")
