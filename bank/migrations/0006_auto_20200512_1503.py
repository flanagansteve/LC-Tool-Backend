# Generated by Django 3.0.3 on 2020-05-12 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0005_auto_20200512_1502'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lcappquestion',
            name='disabled',
            field=models.CharField(blank=True, default='[]', max_length=500),
        ),
    ]
