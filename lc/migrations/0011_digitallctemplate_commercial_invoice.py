# Generated by Django 3.0.3 on 2020-05-27 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0010_auto_20200527_1707'),
    ]

    operations = [
        migrations.AddField(
            model_name='digitallctemplate',
            name='commercial_invoice',
            field=models.CharField(blank=True, default='{}', max_length=100),
        ),
    ]