from django.db import models
from django.contrib.auth.models import Group, User

def pdf_app_path(bank, filename):
    # file will be uploaded to MEDIA_ROOT/bank_<bank_id>/lc_application.pdf
    return 'bank_{0}/lc_application.pdf'.format(instance.bank.id)

# TODO decide whether to store files on our back end, or as a link to a cloud
class Bank(models.Model):
    name = models.CharField(max_length=250)
    # TODO files aint json serialisable king, fix it
    #pdf_application = models.FileField(upload_to=pdf_app_path, blank=True)
    # TODO make this a list? or maybe it already is
    #digital_application = models.ForeignKey(LCAppQuestion, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class BankEmployee(models.Model):
    name = models.CharField(max_length=250, blank=True)
    title = models.CharField(max_length=250, blank=True)
    email = models.CharField(max_length=50)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + ', ' + self.title + ' at ' + str(self.bank)

class LCAppQuestion(models.Model):
    question_text = models.CharField(max_length = 250)
    key_name = models.CharField(max_length = 50)
    type = models.CharField(max_length = 25)
    required = models.BooleanField()
