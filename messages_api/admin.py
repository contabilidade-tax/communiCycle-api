from django.contrib import admin

from messages_api.models import Message, Ticket


class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "contact_number",
        "status",
        "ticket",
        "text",
        "is_from_me",
    )  # Colunas a serem exibidas na lista de objetos no admin


# Register your models here.
admin.site.register(Message, MessageAdmin)
admin.site.register(Ticket)
