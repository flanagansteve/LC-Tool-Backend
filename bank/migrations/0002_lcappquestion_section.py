# Generated by Django 3.0.3 on 2020-05-11 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lcappquestion',
            name='section',
            field=models.CharField(blank=True, default='General', max_length=50),
        ),
    ]
