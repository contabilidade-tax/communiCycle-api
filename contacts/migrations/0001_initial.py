# Generated by Django 4.2.1 on 2023-07-27 16:45

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cnpj', models.CharField(max_length=14, unique=True)),
                ('company_name', models.CharField(max_length=255)),
                ('responsible_name', models.CharField(max_length=255)),
                ('establishment_id', models.IntegerField(blank=True, null=True)),
                ('pdf', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('name', models.CharField(max_length=255, null=True)),
                ('contact_id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('country_code', models.CharField(max_length=3)),
                ('ddd', models.CharField(max_length=2)),
                ('contact_number', models.CharField(max_length=9)),
                ('establishments', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, null=True, size=None)),
                ('company_contacts', models.ManyToManyField(blank=True, related_name='digisac_contacts', to='contacts.companycontact')),
            ],
            options={
                'unique_together': {('contact_number', 'contact_id')},
            },
        ),
        migrations.AddField(
            model_name='companycontact',
            name='contact',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='company_contact', to='contacts.contact'),
        ),
        migrations.CreateModel(
            name='Pendencies',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cnpj', models.CharField(max_length=255)),
                ('period', models.DateField()),
                ('pdf', models.TextField()),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pendencies', to='contacts.companycontact')),
            ],
            options={
                'unique_together': {('cnpj', 'period')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='companycontact',
            unique_together={('cnpj', 'establishment_id')},
        ),
    ]
