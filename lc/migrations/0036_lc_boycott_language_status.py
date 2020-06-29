# Generated by Django 3.0.3 on 2020-06-24 22:43

from django.db import migrations, models
import lc.models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0035_boycottlanguage'),
    ]

    operations = [
        migrations.AddField(
            model_name='lc',
            name='boycott_language_status',
            field=models.CharField(choices=[(lc.models.Status['INC'], 'incomplete'), (lc.models.Status['ACC'], 'accepted'), (lc.models.Status['REJ'], 'rejected'), (lc.models.Status['REQ'], 'requested')], default=lc.models.Status['INC'], max_length=10),
        ),
    ]
