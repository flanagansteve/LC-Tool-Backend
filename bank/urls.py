from django.conf.urls import url
from . import views

urlpatterns = [
    # GET all the banks (TODO: thats probably just for testing)
    # POST to create a bank
    # /bank/
    url(r'^$', views.index, name='index'),

    # GET/PUT/DELETE to Read/Update/Delete banks
    # /bank/{bank_id}
    url(r'^(?P<bank_id>[0-9]+)/$', views.rud_bank, name='rud_bank'),

    # Invite new employee by POST-ing with {email:'some@address.com'}
    # /bank/{bank_id}/invite_teammate
    url(r'^(?P<bank_id>[0-9]+)/invite_teammate', views.invite_teammate, name='invite_teammate'),

    # RUD a bank's employees
    # /bank/{bank_id}/{employee_id}
    url(r'^(?P<bank_id>[0-9]+)/(?P<employee_id>[0-9]+)/$', views.rud_bank_employee, name='rud_bank_employee'),

    # register upon invitiation by supplying the fields of a BankEmployee
    # get back a User
    # /bank/register
    url(r'^(?P<bank_id>[0-9]+)/register$', views.register_upon_invitation, name='register_upon_invitation'),

    # log in
    # /bank/login
    url(r'^(?P<bank_id>[0-9]+)/login$', views.login, name='login')
]
