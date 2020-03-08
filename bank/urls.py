from django.conf.urls import url
from . import views

""" Endpoints:
1. /bank/
# GET all the banks (TODO: thats probably just for testing)
# POST the following to create a bank & first employee
{
    "new_bank_name":"some bank",
    "name":"the first employees name",
    "email":"firstemployeesname@somebank.com",
    "title":"first employees title",
    "password":"FirstEmployeesPassword"
}
# and receive back
{
    "bountium_access_token":"keyboard@dumb.com2020-02-29 16:33:40.776840",
    "objects_created":[
        {
            "model": "bank.bank",
            "pk": [your new banks primary key, which will be used to identify it],
            "fields": {
                "name": "some bank"
            }
        },
        {
            "model": "auth.user",
            "pk": [the id of this user among all bountium bank users, also will be used later],
            "fields": {
                "password": [salted hash of this user's password],
                "last_login": null,
                "is_superuser": false,
                "username": "firstemployeesname@somebank.com",
                "first_name": "",
                "last_name": "",
                "email": "firstemployeesname@somebank.com",
                "is_staff": false,
                "is_active": true,
                "date_joined": "2020-02-29T16:33:40.602Z",
                "groups": [],
                "user_permissions": []
            }
        }
    ]
}

2. /bank/{bank_id}
# GET/PUT/Delete to Read/Update/Delete banks

3. # /bank/{bank_id}/invite_teammate
# POST with
{"invitee_email":"some@address.com"}
# to invite a teammate, and receive back the invitation status as one of:
{
    "status" : "registered" || "invited on [current time as timestamp of invite]" || "re-invited on [current time as timestamp of invite]"
    [and if the employee was successfully registered]
    "employee" : {the employee object with that email}
}

4. /bank/{bank_id}/{employee_id}
# RUD a bank's employees

5. /bank/{bank_id}/register
POST with:
{
TODO
}
to register upon invitation, and receive back
{
TODO
}

6. /bank/{bank_id}/pdf_app
GET to receive back:
pdf_application.pdf

POST, as an employee of the bank, with:
pdf_application.pdf

7. /bank/{bank_id}/digital_app
GET to receive back:
[{ the fields of an ApplicationQuestion }]

POST, as an employee of the bank, with:
[{ the fields of an ApplicationQuestion }]

"""

urlpatterns = [
    # /bank/
    url(r'^$', views.index, name='index'),

    # /bank/{bank_id}
    url(r'^(?P<bank_id>[0-9]+)/$', views.rud_bank, name='rud_bank'),

    # /bank/{bank_id}/invite_teammate
    url(r'^(?P<bank_id>[0-9]+)/invite_teammate', views.invite_teammate, name='invite_teammate'),

    # /bank/{bank_id}/{employee_id}
    url(r'^(?P<bank_id>[0-9]+)/(?P<employee_id>[0-9]+)/$', views.rud_bank_employee, name='rud_bank_employee'),

    # /bank/{bank_id}/register
    url(r'^(?P<bank_id>[0-9]+)/register$', views.register_upon_invitation, name='register_upon_invitation'),

    # TODO
    # /bank/{bank_id}/pdf_app

    # /bank/{bank_id}/digital_app

]
