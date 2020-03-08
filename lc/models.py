from django.db import models
from bank.models import Bank, BankEmployee
from business.models import Business, BusinessEmployee

# Abstract LC from which Pdf and Digital inherit
# TODO add assigning employees to an LC
class LC(models.Model):
    # -- the parties to an LC --
    client = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='client')
    beneficiary = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='beneficiary')
    issuer = models.ForeignKey(Bank, on_delete=models.CASCADE)

    # -- the status of an LC -- #
    # TODO do terms_satisfied & paid_out fields make sense for a Standby LC?
    # theoretically it could be 'satisfied' and 'pay out more than once' -
    # the difference is, of course, that satisfaction is a bad thing
    # and not expected.
        # on one hand, this does work for our purposes and its
        # an elegant framing
        # on the other, if this isn't how people currently think
        # about LCs, it may be counterproductive. This thinking
        # could seep into the UX even if its only meant to be
        # an elegant shortcut on the back end. Idk!
    issuer_approved = models.BooleanField()
    beneficiary_approved = models.BooleanField()
    #TODO: previous_version = models.ForeignKey(LC, )
    terms_satisfied = models.BooleanField()
    requested = models.BooleanField()
    drawn = models.BooleanField()
    paid_out = models.BooleanField()

def pdf_app_response_path(lc, filename):
    # file will be uploaded to MEDIA_ROOT/bank_<id>/client_<id>/applications/%Y/%m/%d/filename
    return 'bank_{0}/client_{1}/applications/%Y/%m/%d/{2}'.format(instance.lc.issuer.id, instance.lc.client.id, filename)

def pdf_lc_contract_path(lc, filename):
    # file will be uploaded to MEDIA_ROOT/bank_<id>/client_<id>/contracts/%Y/%m/%d/filename
    return 'bank_{0}/client_{1}/contracts/%Y/%m/%d/{2}'.format(instance.lc.issuer.id, instance.lc.client.id, filename)

class PdfLC(LC):
    app_response = models.FileField(upload_to=pdf_app_response_path)
    contract = models.FileField(upload_to=pdf_lc_contract_path)

class DigitalLC(LC):
    # -- the actual data of this lc -- #
    # TODO add all the other fields in the SVB template
    # CDM can be ('Courier', 'SWIFT') or other
    credit_delivery_means = models.CharField(max_length=250)
    # Goes up to 1,000T
    credit_amt = models.DecimalField(max_digits=17, decimal_places=2)
    # TODO this should technically be an enum
    currency_denomination = models.CharField(max_length=5, default='USD')
    # TODO this should technically be an enum, one of
    # ['Commercial', 'Standby', 'Import', 'Export']
    type = models.CharField(max_length=20, default='Commercial')

    # TODO someday: def to_pdf()

class DocumentaryRequirement(models.Model):
    for_lc = models.ForeignKey(LC, on_delete=models.CASCADE)
    doc_name = models.CharField(max_length=250)
    # NOTE for now just letting users define the required values
    # as a string, ie:
        # "The inspection grade must be a B+ or higher"
    # enabling manual evaluation. down the line,
    # we should store a mapping of
        # "required_value_name : required_value_value"
    # so that we could intelligently scan a submitted doc req
    # for this value
    required_values = models.CharField(max_length=500)
    due_date = models.DateField()
    link_to_submitted_doc = models.CharField(max_length=250, blank=True)
    complaints = models.CharField(max_length=1000)
    satisfied = models.BooleanField()
