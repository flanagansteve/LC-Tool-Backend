# Generated by Django 3.0.3 on 2020-06-23 04:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0005_remove_business_registered'),
    ]

    operations = [
        migrations.AlterField(
            model_name='business',
            name='country',
            field=models.CharField(default='United States', max_length=250),
        ),
    ]
