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
    "bountium_access_token":"keyboard@dumb.com2020-02-29 16:33:40.776840",
    "objects_created":[
        {
            "model": "business.business",
            "pk": [your new businesss primary key, which will be used to identify it],
            "fields": {
                "name": "some business"
            }
        },
        {
            "model": "auth.user",
            "pk": [the id of this user among all bountium business users, also will be used later],
            "fields": {
                "password": [salted hash of this user's password],
                "last_login": null,
                "is_superuser": false,
                "username": "firstemployeesname@somebusiness.com",
                "first_name": "",
                "last_name": "",
                "email": "firstemployeesname@somebusiness.com",
                "is_staff": false,
                "is_active": true,
                "date_joined": "2020-02-29T16:33:40.602Z",
                "groups": [],
                "user_permissions": []
            }
        }
    ]
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
TODO
}
to register upon invitation, and receive back
{
TODO
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
