# Generated by Django 3.0.3 on 2020-07-23 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0049_auto_20200723_1735'),
    ]

    operations = [
        migrations.AlterField(
            model_name='digitallc',
            name='confirmation_means',
            field=models.CharField(default='No Confirmation', max_length=1000, null=True),
        ),
    ]
