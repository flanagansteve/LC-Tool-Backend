# Generated by Django 3.0.3 on 2020-05-29 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0013_auto_20200528_1756'),
    ]

    operations = [
        migrations.AlterField(
            model_name='digitallctemplate',
            name='exchange_rate_tolerance',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name='digitallctemplate',
            name='insurance_percentage',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=8, null=True),
        ),
    ]
