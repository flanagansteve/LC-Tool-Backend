from django.db import models


# A business working with LCs
# - could be an LC-seeking-business
# - could be an LC-beneficiary
# - could be sometimes one sometimes the other!
from bank.models import Bank


class Business(models.Model):
    name = models.CharField(max_length=250)
    address = models.CharField(max_length=250)

    # Goes up to 999T,999B,999M,999K,999.99
    # NOTE default-ing with dummy values for now
    annual_cashflow = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    balance_available = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    approved_credit = models.ManyToManyField(Bank, through='ApprovedCredit')
    # TODO should be an enum among supported countries
    country = models.CharField(max_length=250, default="USA")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'annual_cashflow': self.annual_cashflow,
            'balance_available': self.balance_available,
            'approved_credit': list(map(lambda x: x.to_dict(), self.approvedcredit_set.all())),
            'country': self.country
        }

    def __str__(self):
        return self.name


class BusinessEmployee(models.Model):
    name = models.CharField(max_length=250, null=True, blank=True)
    title = models.CharField(max_length=250, null=True, blank=True)
    email = models.CharField(max_length=50)
    employer = models.ForeignKey(Business, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + ', ' + self.title + ' at ' + str(self.employer)


class ApprovedCredit(models.Model):
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('bank', 'business')

    approved_credit_amt = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'approved_credit_amt': self.approved_credit_amt,
            'bank': {'id': self.bank.id, 'name': self.bank.name},
            'business': {'id': self.business.id, 'name': self.business.name}
        }
