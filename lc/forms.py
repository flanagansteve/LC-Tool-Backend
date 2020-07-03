from django import forms
from .models import DigitalLC


class BankInitiatedLC(forms.Form):
    def __init__(self, data):
        super().__init__(data=data)
        self.fields['applicant_name'] = forms.CharField(max_length=250)
        self.fields['applicant_employee_contact'] = forms.EmailField(max_length=250)


class DigitalLCForm(forms.ModelForm):
    class Meta:
        model = DigitalLC
        exclude = []
