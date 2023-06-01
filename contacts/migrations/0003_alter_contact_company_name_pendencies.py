# Generated by Django 4.2 on 2023-05-31 17:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0002_contact_company_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='company_name',
            field=models.CharField(default='RAZÃO SOCIAL...', max_length=255),
        ),
        migrations.CreateModel(
            name='Pendencies',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cnpj', models.CharField(max_length=255)),
                ('period', models.DateField()),
                ('pdf', models.TextField()),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pendencies', to='contacts.contact')),
            ],
        ),
    ]