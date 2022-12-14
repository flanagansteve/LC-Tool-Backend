# Generated by Django 3.0.3 on 2020-07-14 16:16

import bank.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0017_lcappquestion_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='bank',
            name='status',
            field=models.CharField(choices=[(bank.models.BankStatus['PEND'], 'Pending'), (bank.models.BankStatus['SET'], 'Setup')], default=bank.models.BankStatus['SET'], max_length=20),
        ),
    ]
