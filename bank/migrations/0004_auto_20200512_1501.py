# Generated by Django 3.0.3 on 2020-05-12 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0003_lcappquestion_disabled'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lcappquestion',
            name='disabled',
            field=models.CharField(blank=True, default=None, max_length=500, null=True),
        ),
    ]
