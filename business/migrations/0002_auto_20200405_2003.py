# Generated by Django 3.0.3 on 2020-04-05 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='business',
            name='country',
            field=models.CharField(default='USA', max_length=250),
        ),
        migrations.AlterField(
            model_name='business',
            name='annual_cashflow',
            field=models.DecimalField(decimal_places=2, default=40000, max_digits=20),
        ),
        migrations.AlterField(
            model_name='business',
            name='approved_credit',
            field=models.DecimalField(decimal_places=2, default=240000, max_digits=20),
        ),
        migrations.AlterField(
            model_name='business',
            name='balance_available',
            field=models.DecimalField(decimal_places=2, default=200000, max_digits=20),
        ),
    ]