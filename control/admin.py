from django.contrib import admin

from control.models import DASFileGrouping, MessageControl, PdfFile, TicketLink

# Register your models here.
admin.site.register(MessageControl)
admin.site.register(TicketLink)
admin.site.register(DASFileGrouping)
admin.site.register(PdfFile)
