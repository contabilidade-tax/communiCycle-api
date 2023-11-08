from django.db import models


class Ticket(models.Model):
    ticket_id = models.CharField(max_length=255, primary_key=True)
    period = models.DateField()
    is_open = models.BooleanField(default=True)
    contact_id = models.CharField(max_length=255)
    last_message_id = models.CharField(max_length=500, default="ndsaujfbnujsafbncuj")

    def __str__(self):
        return f"{self.ticket_id} - {self.period} - {self.is_open}"


class Message(models.Model):
    message_id = models.CharField(max_length=255, primary_key=True)
    contact_id = models.CharField(max_length=255, null=False)
    contact_number = models.CharField(max_length=255, null=False)
    period = models.DateField()
    status = models.IntegerField(
        choices=((0, "Criada"), (1, "Enviada"), (2, "Recebida"), (3, "Visualizada"))
    )
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="messages"
    )
    message_type = models.CharField(max_length=255)
    is_from_me = models.BooleanField(default=False)
    text = models.CharField(max_length=500)
    retries = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.message_id} - {self.period} - {self.status}"

    class Meta:
        unique_together = (("contact_id", "message_id"),)
