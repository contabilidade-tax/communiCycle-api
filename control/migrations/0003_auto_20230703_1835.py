# Generated by Django 2.2.28 on 2023-07-03 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('control', '0002_dasfilegrouping'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dasfilegrouping',
            name='companies',
            field=models.ManyToManyField(blank=True, to='contacts.CompanyContact'),
        ),
    ]