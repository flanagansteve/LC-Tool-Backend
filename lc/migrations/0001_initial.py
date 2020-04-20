# Generated by Django 3.0.3 on 2020-04-20 01:35

from django.db import migrations, models
import django.db.models.deletion
import lc.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bank', '__first__'),
        ('business', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentaryRequirement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_name', models.CharField(max_length=250)),
                ('required_values', models.CharField(blank=True, max_length=500, null=True)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('link_to_submitted_doc', models.CharField(blank=True, max_length=250, null=True)),
                ('satisfied', models.BooleanField(default=False)),
                ('submitted_doc_complaints', models.CharField(blank=True, max_length=1000, null=True)),
                ('modified_and_awaiting_beneficiary_approval', models.BooleanField(default=False)),
                ('modification_complaints', models.CharField(blank=True, max_length=1000, null=True)),
                ('rejected', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='LC',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_approved', models.BooleanField(default=True)),
                ('issuer_approved', models.BooleanField(default=False)),
                ('beneficiary_approved', models.BooleanField(default=False)),
                ('latest_version_notes', models.CharField(blank=True, max_length=1000, null=True)),
                ('application_date', models.DateField(blank=True, null=True)),
                ('terms_satisfied', models.BooleanField(default=False)),
                ('requested', models.BooleanField(default=False)),
                ('drawn', models.BooleanField(default=False)),
                ('paid_out', models.BooleanField(default=False)),
                ('account_party', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lc_lc_account_party', to='business.Business')),
                ('advising_bank', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lc_lc_advising_bank', to='bank.Bank')),
                ('beneficiary', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lc_lc_beneficiary', to='business.Business')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lc_lc_client', to='business.Business')),
                ('issuer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lc_lc_issuer', to='bank.Bank')),
                ('tasked_account_party_employees', models.ManyToManyField(related_name='lc_lc_tasked_account_party_employees', to='business.BusinessEmployee')),
                ('tasked_advising_bank_employees', models.ManyToManyField(related_name='lc_lc_tasked_advising_bank_employees', to='bank.BankEmployee')),
                ('tasked_beneficiary_employees', models.ManyToManyField(related_name='lc_lc_tasked_beneficiary_employees', to='business.BusinessEmployee')),
                ('tasked_client_employees', models.ManyToManyField(related_name='lc_lc_tasked_client_employees', to='business.BusinessEmployee')),
                ('tasked_issuer_employees', models.ManyToManyField(related_name='lc_lc_tasked_issuer_employees', to='bank.BankEmployee')),
            ],
        ),
        migrations.CreateModel(
            name='CharterPartyBillOfLadingRequirement',
            fields=[
                ('documentaryrequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.DocumentaryRequirement')),
                ('carrying_vessel', models.CharField(blank=True, max_length=500, null=True)),
                ('signed_by_master_owner_charterer', models.BooleanField(default=False)),
                ('port_of_loading', models.CharField(blank=True, max_length=500, null=True)),
                ('date_of_issuance', models.DateField(blank=True, null=True)),
                ('indicated_date_of_shipment', models.DateField(blank=True, null=True)),
                ('port_of_destination', models.CharField(blank=True, max_length=500, null=True)),
            ],
            bases=('lc.documentaryrequirement',),
        ),
        migrations.CreateModel(
            name='CommercialInvoiceRequirement',
            fields=[
                ('documentaryrequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.DocumentaryRequirement')),
                ('invoice_issuer', models.CharField(blank=True, max_length=500, null=True)),
                ('recipient', models.CharField(blank=True, max_length=500, null=True)),
                ('currency', models.CharField(blank=True, max_length=500, null=True)),
                ('goods_description', models.CharField(blank=True, max_length=500, null=True)),
            ],
            bases=('lc.documentaryrequirement',),
        ),
        migrations.CreateModel(
            name='CourierReceiptRequirement',
            fields=[
                ('documentaryrequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.DocumentaryRequirement')),
                ('courier_name', models.CharField(blank=True, max_length=500, null=True)),
                ('stamped_or_signed_by_courier', models.BooleanField(default=False)),
                ('stamping_or_signing_location', models.CharField(blank=True, max_length=500, null=True)),
                ('date_of_pickup', models.DateField(blank=True, null=True)),
            ],
            bases=('lc.documentaryrequirement',),
        ),
        migrations.CreateModel(
            name='DigitalLC',
            fields=[
                ('lc_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.LC')),
                ('type', models.CharField(default='Commercial', max_length=20)),
                ('credit_delivery_means', models.CharField(blank=True, max_length=250, null=True)),
                ('credit_amt_verbal', models.CharField(blank=True, max_length=250, null=True)),
                ('credit_amt', models.DecimalField(blank=True, decimal_places=2, max_digits=17, null=True)),
                ('currency_denomination', models.CharField(default='USD', max_length=5)),
                ('applicant_and_ap_j_and_s_obligated', models.BooleanField(blank=True, null=True)),
                ('forex_contract_num', models.CharField(blank=True, max_length=250, null=True)),
                ('exchange_rate_tolerance', models.DecimalField(blank=True, decimal_places=5, max_digits=8, null=True)),
                ('purchased_item', models.CharField(blank=True, max_length=1000, null=True)),
                ('units_of_measure', models.CharField(blank=True, max_length=1000, null=True)),
                ('units_purchased', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('unit_error_tolerance', models.DecimalField(blank=True, decimal_places=5, max_digits=8, null=True)),
                ('confirmation_means', models.CharField(default='No Confirmation', max_length=1000)),
                ('expiration_date', models.DateField(blank=True, null=True)),
                ('draft_presentation_date', models.DateField(blank=True, null=True)),
                ('drafts_invoice_value', models.DecimalField(decimal_places=5, default=1.0, max_digits=8)),
                ('credit_availability', models.CharField(blank=True, max_length=250, null=True)),
                ('deferred_payment_date', models.DateField(blank=True, null=True)),
                ('partial_shipment_allowed', models.BooleanField(default=False)),
                ('transshipment_allowed', models.BooleanField(default=False)),
                ('merch_charge_location', models.CharField(blank=True, max_length=250, null=True)),
                ('late_charge_date', models.DateField(blank=True, null=True)),
                ('charge_transportation_location', models.CharField(blank=True, max_length=250, null=True)),
                ('incoterms_to_show', models.CharField(blank=True, max_length=250, null=True)),
                ('named_place_of_destination', models.CharField(blank=True, max_length=250, null=True)),
                ('doc_reception_notifees', models.CharField(blank=True, max_length=250, null=True)),
                ('arranging_own_insurance', models.BooleanField(default=False)),
                ('other_instructions', models.CharField(blank=True, max_length=2000, null=True)),
                ('merch_description', models.CharField(blank=True, max_length=2000, null=True)),
                ('transferable_to_applicant', models.BooleanField(default=False)),
                ('transferable_to_beneficiary', models.BooleanField(default=False)),
                ('other_data', models.CharField(max_length=1000)),
                ('credit_expiry_location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lc_digitallc_credit_expiry_location', to='bank.Bank')),
                ('delegated_negotiating_banks', models.ManyToManyField(to='bank.Bank')),
                ('paying_acceptance_and_discount_charges', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lc_digitallc_paying_acceptance_and_discount_charges', to='business.Business')),
                ('paying_other_banks_fees', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lc_digitallc_paying_other_banks_fees', to='business.Business')),
            ],
            bases=('lc.lc',),
        ),
        migrations.CreateModel(
            name='InsuranceDocumentRequirement',
            fields=[
                ('documentaryrequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.DocumentaryRequirement')),
                ('issued_by_insurer', models.BooleanField(default=False)),
                ('all_originals_present', models.BooleanField(default=False)),
                ('is_not_cover_note', models.BooleanField(default=False)),
                ('covered_prior_to_shipment', models.BooleanField(default=False)),
                ('coverage_amt', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
            ],
            bases=('lc.documentaryrequirement',),
        ),
        migrations.CreateModel(
            name='PdfLC',
            fields=[
                ('lc_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.LC')),
                ('app_response', models.FileField(upload_to=lc.models.pdf_app_response_path)),
                ('contract', models.FileField(upload_to=lc.models.pdf_lc_contract_path)),
            ],
            bases=('lc.lc',),
        ),
        migrations.CreateModel(
            name='PostReceiptRequirement',
            fields=[
                ('documentaryrequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.DocumentaryRequirement')),
                ('courier_name', models.CharField(blank=True, max_length=500, null=True)),
                ('stamped_or_signed_by_courier', models.BooleanField(default=False)),
                ('stamping_or_signing_location', models.CharField(blank=True, max_length=500, null=True)),
                ('date_of_stamping', models.DateField(blank=True, null=True)),
            ],
            bases=('lc.documentaryrequirement',),
        ),
        migrations.CreateModel(
            name='TransportDocumentRequirement',
            fields=[
                ('documentaryrequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.DocumentaryRequirement')),
                ('carrier_name', models.CharField(blank=True, max_length=500, null=True)),
                ('signed_by_carrier_or_master', models.BooleanField(default=False)),
                ('references_tandc_of_carriage', models.BooleanField(default=False)),
                ('date_of_issuance', models.DateField(blank=True, null=True)),
                ('indicated_date_of_shipment', models.DateField(blank=True, null=True)),
            ],
            bases=('lc.documentaryrequirement',),
        ),
        migrations.AddField(
            model_name='documentaryrequirement',
            name='for_lc',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lc.LC'),
        ),
        migrations.CreateModel(
            name='AirTransportDocument',
            fields=[
                ('transportdocumentrequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.TransportDocumentRequirement')),
                ('accepted_for_carriage', models.BooleanField(default=False)),
                ('airport_of_departure', models.CharField(blank=True, max_length=500, null=True)),
                ('airport_of_destination', models.CharField(blank=True, max_length=500, null=True)),
            ],
            bases=('lc.transportdocumentrequirement',),
        ),
        migrations.CreateModel(
            name='BillOfLadingRequirement',
            fields=[
                ('transportdocumentrequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.TransportDocumentRequirement')),
                ('port_of_loading', models.CharField(blank=True, max_length=500, null=True)),
                ('noncommital_shipment_indication_with_no_update', models.BooleanField(default=True)),
                ('port_of_destination', models.CharField(blank=True, max_length=500, null=True)),
                ('subject_to_charter_party', models.BooleanField(default=False)),
            ],
            bases=('lc.transportdocumentrequirement',),
        ),
        migrations.CreateModel(
            name='MultimodalTransportDocumentRequirement',
            fields=[
                ('transportdocumentrequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.TransportDocumentRequirement')),
                ('place_of_dispatch', models.CharField(blank=True, max_length=500, null=True)),
                ('place_of_destination', models.CharField(blank=True, max_length=500, null=True)),
                ('subject_to_charter_party', models.BooleanField(default=False)),
            ],
            bases=('lc.transportdocumentrequirement',),
        ),
        migrations.CreateModel(
            name='RoadRailInlandWaterwayTransportDocumentsRequirement',
            fields=[
                ('transportdocumentrequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.TransportDocumentRequirement')),
                ('stamped_by_rail_co', models.BooleanField(default=False)),
                ('place_of_shipment', models.CharField(blank=True, max_length=500, null=True)),
                ('place_of_destination', models.CharField(blank=True, max_length=500, null=True)),
            ],
            bases=('lc.transportdocumentrequirement',),
        ),
        migrations.CreateModel(
            name='LCAppQuestionResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_json_value', models.CharField(max_length=5000)),
                ('for_question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bank.LCAppQuestion')),
                ('for_lc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lc.DigitalLC')),
            ],
        ),
        migrations.CreateModel(
            name='NonNegotiableSeaWaybillRequirement',
            fields=[
                ('billofladingrequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lc.BillOfLadingRequirement')),
            ],
            bases=('lc.billofladingrequirement',),
        ),
    ]
