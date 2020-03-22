from django.conf.urls import url
from . import views

"""
1./user/login
POST with:
{
"email":"someuser@somebank.com",
"password":"theuserspassword"
}
to log in, and receive back
{
TODO document this
}

2. /user/logout
POST to log out, and receive back
{
"success": true
}, or 403 for bad credentials

3. /user/change_password
POST a new password:
{
"new_password" : "thenewpassword123"
}
and receive back
{
"success": true
}, or 403 for bad credentials
"""

urlpatterns = [

    # /user/login
    url(r'^login/$', views.user_login, name='user_login'),

    # /user/logout
    url(r'^logout/$', views.user_logout, name='user_logout'),

    # /user/logout
    url(r'^change_password/$', views.change_password, name='change_password')
]
