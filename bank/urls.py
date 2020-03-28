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
    "session_expiry":request.session.get_expiry_date(),
    "user_employee":{the BankEmployee of this user},
    "users_employer":{the Bank this user just created}
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
    'email'
    'password'
    'name'
    'title'
}
to register upon invitation, and receive back
{
    "session_expiry":request.session.get_expiry_date(),
    "user_employee":{the BankEmployee of this user},
    "users_employer":{the Bank this user just created}
}

6. /bank/{bank_id}/pdf_app
GET to receive back:
pdf_application.pdf

POST, as an employee of the bank, with:
pdf_application.pdf

7. /bank/{bank_id}/digital_app
GET to receive back:

POST, as an employee of the bank, with:
[{ the fields of an ApplicationQuestion }]
to add more questions to your bank's lc application

8. /bank/{bank_id}/digital_app/{question_id}
DeLETE as an employee of the bank to delete a non-default question

PUT as an employee of the bank with:
[{ the fields of an ApplicationQuestion }]
to modify a non-default question
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
    url(r'^(?P<bank_id>[0-9]+)/digital_app$', views.digital_app, name='digital_app'),


]
