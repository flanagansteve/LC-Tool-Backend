# Generated by Django 3.0.3 on 2020-04-24 01:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lc', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='commercialinvoicerequirement',
            old_name='recipient',
            new_name='buyer_name',
        ),
        migrations.RenameField(
            model_name='commercialinvoicerequirement',
            old_name='invoice_issuer',
            new_name='invoice_issuer_name',
        ),
        migrations.RemoveField(
            model_name='insurancedocumentrequirement',
            name='all_originals_present',
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='additional_comments',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='buyer_address',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='consignee_address',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='consignee_name',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='country_of_export',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='country_of_origin',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='declaration_statement',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='hs_code',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='incoterm_of_sale',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='indicated_date_of_shipment',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='invoice_issuer_address',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='invoice_total',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='reason_for_export',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='signature',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='total_value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='unit_value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='units',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='commercialinvoicerequirement',
            name='units_of_measure',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='documentaryrequirement',
            name='type',
            field=models.CharField(default='generic', max_length=50),
        ),
        migrations.AlterField(
            model_name='commercialinvoicerequirement',
            name='currency',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]