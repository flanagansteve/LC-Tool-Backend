# Generated by Django 3.0.3 on 2020-06-23 15:27

from django.db import migrations, models
import lc.models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0033_auto_20200623_0731'),
    ]

    operations = [
        migrations.AddField(
            model_name='lc',
            name='import_license_approval',
            field=models.CharField(choices=[(lc.models.Status['INC'], 'incomplete'), (lc.models.Status['ACC'], 'accepted'), (lc.models.Status['REJ'], 'rejected'), (lc.models.Status['REQ'], 'requested')], default=lc.models.Status['INC'], max_length=10),
        ),
    ]
