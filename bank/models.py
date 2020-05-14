from django.db import models
from django.forms.models import model_to_dict

# TODO should we reflect article 36, that a bank might interrupt business due to acts of god / war / etc and fail to honour credits that expire in the interim? allow a bank to 'go inactive'

class LCAppQuestion(models.Model):
    question_text = models.CharField(max_length = 250)
    key = models.CharField(max_length = 50)
    type = models.CharField(max_length = 25)
    required = models.BooleanField()
    # Used for type=radio or type=checkbox questions; blank for all others
    # The internet says the best way to do a list of strs as a django field
    # (w/o making a class of literally just a string)
    # is, to literally, make a separated-value string...
    # and re/denormalise it whenever needed : ( wtf
    # https://stackoverflow.com/questions/1110153/what-is-the-most-efficient-way-to-store-a-list-in-the-django-models
    options = models.CharField(max_length = 500, blank=True, default=True)
    section = models.CharField(max_length = 50, blank=True, default="General")
    disabled = models.CharField(max_length = 500, blank=True, default='')

def pdf_app_path(bank, filename):
    # file will be uploaded to MEDIA_ROOT/bank_<bank_id>/lc_application.pdf
    return 'bank_{0}/lc_application.pdf'.format(instance.bank.id)

# TODO decide whether to store files on our back end, or as a link to a cloud
class Bank(models.Model):
    name = models.CharField(max_length=250)
    # TODO files aint json serialisable king, fix it
    #pdf_application = models.FileField(upload_to=pdf_app_path, blank=True)
    # The following are null-able to account for Advising Banks to an LC -
    # they aren't using Bountium but must be looped in on an LC
    # TODO make this a list? or maybe it already is
    digital_application = models.ManyToManyField(LCAppQuestion)
    using_digital_app = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    # Using because django's JSON serialiser doesnt like nested
    # serialising into LCAppQuestion
    def to_dict(self):
        return {
            'name' : self.name,
            'id' : self.id,
            'digital_application' : self.get_lc_app(),
            'using_digital_app' : self.using_digital_app
        }

    def get_lc_app(self):
        to_return = []
        for question in self.digital_application.all():
            to_return.append(model_to_dict(question))
        return to_return

class BankEmployee(models.Model):
    name = models.CharField(max_length=250, null=True, blank=True)
    title = models.CharField(max_length=250, null=True, blank=True)
    email = models.CharField(max_length=50)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + ', ' + self.title + ' at ' + str(self.bank)
