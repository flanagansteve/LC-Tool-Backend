# Generated by Django 3.0.3 on 2020-07-16 16:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0019_auto_20200714_2259'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bank',
            old_name='emailContact',
            new_name='email_contact',
        ),
        migrations.RenameField(
            model_name='bank',
            old_name='mailingAddress',
            new_name='mailing_address',
        ),
    ]
