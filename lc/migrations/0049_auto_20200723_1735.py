# Generated by Django 3.0.3 on 2020-07-23 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0048_lc_advising_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lc',
            name='advising_type',
            field=models.IntegerField(null=True),
        ),
    ]
