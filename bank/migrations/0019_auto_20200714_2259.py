# Generated by Django 3.0.3 on 2020-07-14 22:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0018_bank_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='bank',
            name='country',
            field=models.CharField(default='', max_length=250),
        ),
        migrations.AddField(
            model_name='bank',
            name='emailContact',
            field=models.CharField(default='', max_length=250),
        ),
        migrations.AddField(
            model_name='bank',
            name='mailingAddress',
            field=models.CharField(default='', max_length=250),
        ),
        migrations.AddField(
            model_name='bank',
            name='website',
            field=models.CharField(default='', max_length=250),
        ),
    ]
