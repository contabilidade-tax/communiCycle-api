# Generated by Django 2.2.28 on 2023-07-03 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0002_auto_20230627_1549'),
    ]

    operations = [
        migrations.AddField(
            model_name='companycontact',
            name='pdf',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='companycontact',
            unique_together={('cnpj', 'establishment_id')},
        ),
    ]
