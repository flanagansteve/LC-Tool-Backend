# Generated by Django 3.0.3 on 2020-06-30 17:25

import business.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0006_auto_20200623_0418'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorizedBanks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank', models.CharField(blank=True, max_length=250, null=True)),
                ('status', models.CharField(choices=[(business.models.AuthStatus['AUTH'], 'Authorized'), (business.models.AuthStatus['UNAUTH'], 'Unauthorized')], default=business.models.AuthStatus['UNAUTH'], max_length=10)),
            ],
        ),
        migrations.AddField(
            model_name='businessemployee',
            name='authorized_banks',
            field=models.ManyToManyField(to='business.AuthorizedBanks'),
        ),
    ]
