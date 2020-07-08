from django import forms

from .models import DigitalLC


class BankInitiatedLC(forms.Form):
    def __init__(self, data):
        super().__init__(data=data)
        self.fields['applicant_name'] = forms.CharField(max_length=250)
        self.fields['applicant_employee_contact'] = forms.EmailField(max_length=250)


class DigitalLCBaseForm(forms.ModelForm):
    class Meta:
        model = DigitalLC
        fields = ['credit_delivery_means', 'credit_amt_verbal', 'credit_amt', 'cash_secure', 'currency_denomination',
                  'forex_contract_num', 'purchased_item', 'hts_code',
                  'unit_of_measure', 'units_purchased', 'unit_error_tolerance', 'confirmation_means', 'expiration_date',
                  'credit_availability', 'deferred_payment_date', 'partial_shipment_allowed', 'transshipment_allowed',
                  'merch_charge_location', 'charge_transportation_location', 'named_place_of_destination',
                  'arranging_own_insurance', 'merch_description']


class DigitalLCForm(forms.Form):
    def __init__(self, data):
        super().__init__(data=data)
        self.fields['applicant_name'] = forms.CharField(max_length=250)
        self.fields['applicant_address'] = forms.CharField(max_length=250)
        self.fields['applicant_country'] = forms.CharField(max_length=250)

    applicant_name = forms.CharField(max_length=250)
    applicant_address = forms.CharField(max_length=250)
    applicant_country = forms.CharField(max_length=250)
    beneficiary_name = forms.CharField(max_length=250)
    beneficiary_address = forms.CharField(max_length=250)
    beneficiary_country = forms.CharField(max_length=250)
    account_party = forms.BooleanField()
    applicant_and_ap_j_and_s_obligated = forms.BooleanField(required=False)
    account_party_name = forms.CharField(max_length=250, required=False)
    account_party_address = forms.CharField(max_length=250, required=False)
    exchange_rate_tolerance = forms.DecimalField(required=False)

    def clean(self):
        super().clean()
        if self.cleaned_data.get("account_party"):
            if self.cleaned_data.get("applicant_and_ap_j_and_s_obligated", None) is None:
                self.add_error("applicant_and_ap_j_and_s_obligated",
                               "Missing required field 'applicant_and_ap_j_and_s_obligated'")
            if self.cleaned_data.get("account_party_name", None) is None:
                self.add_error("account_party_name", "Missing required field 'account_party_name")
            if self.cleaned_data.get("account_party_address", None) is None:
                self.add_error("account_party_address", "Missing required field 'account_party_address")

