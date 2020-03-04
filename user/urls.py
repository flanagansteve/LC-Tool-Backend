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
TODO
}

2. /user/logout
POST to log out, and receive back
{
"success": true
}, or 403 for bad credentials
"""

urlpatterns = [

    # /user/login
    url(r'^login/$', views.user_login, name='user_login'),

    # /user/logout
    url(r'^logout/$', views.user_logout, name='user_logout')
]
