# Generated by Django 3.0.3 on 2020-04-24 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0002_auto_20200424_0147'),
    ]

    operations = [
        migrations.RenameField(
            model_name='commercialinvoicerequirement',
            old_name='incoterm_of_sale',
            new_name='incoterms_of_sale',
        ),
        migrations.RenameField(
            model_name='commercialinvoicerequirement',
            old_name='invoice_issuer_address',
            new_name='seller_address',
        ),
        migrations.RenameField(
            model_name='commercialinvoicerequirement',
            old_name='invoice_issuer_name',
            new_name='seller_name',
        ),
        migrations.RenameField(
            model_name='commercialinvoicerequirement',
            old_name='unit_value',
            new_name='unit_price',
        ),
        migrations.RenameField(
            model_name='commercialinvoicerequirement',
            old_name='units',
            new_name='units_purchased',
        ),
        migrations.RemoveField(
            model_name='commercialinvoicerequirement',
            name='invoice_total',
        ),
        migrations.RemoveField(
            model_name='commercialinvoicerequirement',
            name='total_value',
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='date_of_issuance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='signatory_title',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='carrier_address',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='consignee_address',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='consignee_name',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='container_id',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='freight_payment',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='goods_description',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='gross_weight',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='notifee_address',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='notifee_name',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='port_of_discharge',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='port_of_loading',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='signatory_title',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='signature',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='multimodaltransportdocumentrequirement',
            name='vessel_and_voyage',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='commercialinvoicerequirement',
            name='reason_for_export',
            field=models.CharField(default='Sale', max_length=50),
        ),
    ]
