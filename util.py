import csv
import decimal
import urllib.request

from lc.models import SpeciallyDesignatedNational, \
  SpeciallyDesignatedNationalAddress, SpeciallyDesignatedNationalAlternate


def update_django_instance_with_subset_json(json_data, obj):
    for key in json_data:
        if key in dir(obj) and json_data[key]:
            if 'decimal.Decimal' in str(type(getattr(obj, key))):
                setattr(obj, key, decimal.Decimal(str(json_data[key])))
            else:
                setattr(obj, key, json_data[key])
        else:
            # TODO log a bad field but dont flip out
            pass


def update_ofac():
    url = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req)
    response = response.read().decode("utf-8").splitlines()
    cr = csv.reader(response)
    for row in cr:
        if len(row) == 12:
            if SpeciallyDesignatedNational.objects.filter(id=row[0]).exists():
                continue
            for colIndex, col in enumerate(row):
                if col == '-0- ':
                    row[colIndex] = None
            SpeciallyDesignatedNational(id=row[0],
                                        name=row[1],
                                        cleansed_name=row[1].replace(",", "").replace(".", ""),
                                        type=row[2],
                                        program=row[3],
                                        title=row[4],
                                        call_sign=row[5],
                                        vessel_type=row[6],
                                        tonnage=row[7],
                                        grt=row[8],
                                        vessel_flag=row[9],
                                        vessel_owner=row[10],
                                        remarks=row[11]).save()
    url = "https://www.treasury.gov/ofac/downloads/add.csv"
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req)
    response = response.read().decode("utf-8").splitlines()
    cr = csv.reader(response)
    for row in cr:
        if len(row) == 6:
            if SpeciallyDesignatedNationalAddress.objects.filter(id=row[1]).exists():
                continue
            for colIndex, col in enumerate(row):
                if col == '-0- ':
                    row[colIndex] = None
            SpeciallyDesignatedNationalAddress(id=row[1],
                                               sdn_id=row[0],
                                               address=row[2],
                                               address_group=row[3],
                                               country=row[4],
                                               remarks=row[5]).save()
    url = "https://www.treasury.gov/ofac/downloads/alt.csv"
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req)
    response = response.read().decode("utf-8").splitlines()
    cr = csv.reader(response)
    for row in cr:
        if len(row) == 5:
            if SpeciallyDesignatedNationalAlternate.objects.filter(id=row[1]).exists():
                continue
            for colIndex, col in enumerate(row):
                if col == '-0- ':
                    row[colIndex] = None
            SpeciallyDesignatedNationalAlternate(id=row[1],
                                                 sdn_id=row[0],
                                                 type=row[2],
                                                 name=row[3],
                                                 cleansed_name=row[3].replace(",", "").replace(".", ""),
                                                 remarks=row[4]).save()


