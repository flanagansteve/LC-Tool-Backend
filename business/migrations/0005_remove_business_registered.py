# Generated by Django 3.0.3 on 2020-06-11 19:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0004_auto_20200611_1944'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='business',
            name='registered',
        ),
    ]