from django.db import models

# A business working with LCs
# - could be an LC-seeking-business
# - could be an LC-beneficiary
# - could be sometimes one sometimes the other!
class Business(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name

    def to_json(self):
        json = '{'
        json += '\"id\":' + str(self.id) + ','
        json += '\"name\":\"' + self.name + '\"'
        json += '}'
        return json

class BusinessEmployee(models.Model):
    name = models.CharField(max_length=250, blank=True)
    title = models.CharField(max_length=250, blank=True)
    email = models.CharField(max_length=50)
    employer = models.ForeignKey(Business, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + ', ' + self.title + ' at ' + str(self.employer)

    def to_json(self):
        json = '{'
        json += '\"id\":' + str(self.id) + ','
        json += '\"name\":\"' + self.name + '\",'
        json += '\"title\":\"' + self.title + '\",'
        json += '\"employer\":\"' + str(self.employer) + "\""
        json += '}'
        return json
