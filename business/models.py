from django.db import models

# A business working with LCs
# - could be an LC-seeking-business
# - could be an LC-beneficiary
# - could be sometimes one sometimes the other!
class Business(models.Model):
    name = models.CharField(max_length=250)
    address = models.CharField(max_length=250)

    # Goes up to 999T,999B,999M,999K,999.99
    annual_cashflow = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    balance_available = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    approved_credit = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name

class BusinessEmployee(models.Model):
    name = models.CharField(max_length=250, null=True, blank=True)
    title = models.CharField(max_length=250, null=True, blank=True)
    email = models.CharField(max_length=50)
    employer = models.ForeignKey(Business, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + ', ' + self.title + ' at ' + str(self.employer)
