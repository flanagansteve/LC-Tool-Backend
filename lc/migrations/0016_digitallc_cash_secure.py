# Generated by Django 3.0.3 on 2020-06-03 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0015_auto_20200529_2246'),
    ]

    operations = [
        migrations.AddField(
            model_name='digitallc',
            name='cash_secure',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=17),
        ),
    ]
