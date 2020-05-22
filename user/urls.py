from django.conf.urls import url
from . import views

"""
1./user/login/
POST with:
{
"email":"someuser@somebank.com",
"password":"theuserspassword"
}
to log in, and receive back
{
    "session_expiry" : request.session.get_expiry_date(),
    "user_employee" : {this user's employee instance},
    "users_employer" : {this user's employer's bank or biz instance}
}

2. /user/logout/
POST to log out, and receive back
{
"success": true
}, or 403 for bad credentials.py

3. /user/change_password/
POST a new password:
{
"new_password" : "thenewpassword123"
}
and receive back
{
"success": true
}, or 403 for bad credentials.py

4. /user/this_users_info/
GET, as a logged-in user,
{
    "session_expiry" : request.session.get_expiry_date(),
    "user_employee" : {this user's employee instance},
    "users_employer" : {this user's employer's bank or biz instance}
}
"""

urlpatterns = [

    # /user/login/
    url(r'^login/$', views.user_login, name='user_login'),

    # /user/logout/
    url(r'^logout/$', views.user_logout, name='user_logout'),

    # /user/logout/
    url(r'^change_password/$', views.change_password, name='change_password'),

    # /user/this_users_info/
    url(r'^this_users_info/$', views.this_users_info, name='this_users_info')
]
