import decimal


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
