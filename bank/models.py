from django.db import models
from django.contrib.auth.models import Group, User

class Bank(models.Model):
    name = models.CharField(max_length=250)
    pdfApplicationLink = models.CharField(max_length=250)
    # TODO what should the on_delete for this be?
    digitalApplication = models.ForeignKey(DigitalLCApplication, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def to_json(self):
        json = '{'
        json += '\"id\":' + str(self.id) + ','
        json += '\"name\":\"' + self.name + '\"'
        json += '}'
        return json

class BankEmployee(models.Model):
    name = models.CharField(max_length=250, blank=True)
    title = models.CharField(max_length=250, blank=True)
    email = models.CharField(max_length=50)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + ', ' + self.title + ' at ' + str(self.bank)

    def to_json(self):
        json = '{'
        json += '\"id\":' + str(self.id) + ','
        json += '\"name\":\"' + self.name + '\",'
        json += '\"title\":\"' + self.title + '\",'
        json += '\"bank\":\"' + str(self.bank) + "\""
        json += '}'
        return json

# TODO what should the max length of each of these text fields below be?
class DigitalLCApplication(models.Model):
    # We store an application as JSON array of objects; the format is
    """
    {
        'question_text':'the text of the question',
        'answer_type':'integer' || 'decimal' || 'text' etc,
        'required':true || false
    }
    """
    appAsJson = models.CharField(max_length=1000)
