# Generated by Django 3.0.3 on 2020-06-22 23:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0025_auto_20200622_2253'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='author_type',
        ),
    ]
