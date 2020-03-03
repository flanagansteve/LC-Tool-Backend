from django.db import models
from business.models import Business
from bank.models import Bank, BankEmployee
from business.models import Business, BusinessEmployee

class LC(models.Model):
    # TODO should these cascade on delete or not?
    client = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='client')
    beneficiary = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='beneficiary')
    issuer = models.ForeignKey(Bank, on_delete=models.CASCADE)
    # CDM can be ('Courier', 'SWIFT') or other
    credit_delivery_means = models.CharField(max_length=250)
    # Goes up to 1,000T
    credit_amt = models.DecimalField(max_digits=17, decimal_places=2)
    # TODO this should technically be an enum
    currency_denomination = models.CharField(max_length=5, default='USD')
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
    terms_satisfied = models.BooleanField()
    paid_out = models.BooleanField()
    # TODO this should technically be an enum, one of
    # ['Commercial', 'Standby', 'Import', 'Export']
    currency_denomination = models.CharField(max_length=20, default='Commercial')

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
    # TODO how to store a document file?
    #submitted_doc = models.
    satisfied = models.BooleanField()
