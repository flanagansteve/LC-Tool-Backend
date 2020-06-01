# Generated by Django 3.0.3 on 2020-05-29 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0014_auto_20200529_2144'),
    ]

    operations = [
        migrations.AlterField(
            model_name='digitallctemplate',
            name='confirmation_means',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='digitallctemplate',
            name='credit_expiry_location',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='digitallctemplate',
            name='paying_acceptance_and_discount_charges',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='digitallctemplate',
            name='paying_other_banks_fees',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]