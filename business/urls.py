from django.conf.urls import url
from . import views

""" Endpoints:
1. /business/
# GET all the businesses (TODO: thats probably just for testing)
# POST the following to create a business & first employee
{
    "new_business_name":"some business",
    "name":"the first employees name",
    "email":"firstemployeesname@somebusiness.com",
    "title":"first employees title",
    "password":"FirstEmployeesPassword"
}
# and receive back
{
    "session_expiry" : request.session.get_expiry_date(),
    "user_employee" : model_to_dict(business.businessemployee_set.get(email=json_data['email'])),
    "users_employer" : model_to_dict(business)
}

2. /business/{business_id}
# GET/PUT/Delete to Read/Update/Delete businesses

3. # /business/{business_id}/invite_teammate
# POST with
{"invitee_email":"some@address.com"}
# to invite a teammate, and receive back the invitation status as one of:
{
    "status" : "registered" || "invited on [current time as timestamp of invite]" || "re-invited on [current time as timestamp of invite]"
    [and if the employee was successfully registered]
    "employee" : {the employee object with that email}
}

4. /business/{business_id}/{employee_id}
# RUD a business's employees

5. /business/{business_id}/register
POST with:
{
    'email'
    'password'
    'name'
    'title'
}
to register upon invitation, and receive back
{
    'bountium_access_token'
    'user_employee' : { business employee obj }
    'users_employer : { business obj }
}
"""

urlpatterns = [
    # /business/
    url(r'^$', views.index, name='index'),

    # /business/{business_id}
    url(r'^(?P<business_id>[0-9]+)/$', views.rud_business, name='rud_business'),

    # /business/{business_id}/invite_teammate
    url(r'^(?P<business_id>[0-9]+)/invite_teammate', views.invite_teammate, name='invite_teammate'),

    # /business/{business_id}/{employee_id}
    url(r'^(?P<business_id>[0-9]+)/(?P<employee_id>[0-9]+)/$', views.rud_business_employee, name='rud_business_employee'),

    # /business/{business_id}/register
    url(r'^(?P<business_id>[0-9]+)/register$', views.register_upon_invitation, name='register_upon_invitation')
]
