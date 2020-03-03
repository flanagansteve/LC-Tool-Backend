from django.conf.urls import url
from . import views

""" Endpoints:
1. /lc/
# GET all the lcs (TODO: thats probably just for testing)
# POST (TODO: who gets to POST these?) the following to create an LC
{
    TODO
}
# and receive back
{
    TODO
}

2. /lc/{lc_id}
# GET/PUT/Delete to Read/Update/Delete lcs


TODO more
"""

urlpatterns = [
    # /lc/
    url(r'^$', views.index, name='index'),

    # /lc/{lc_id}
    url(r'^(?P<lc_id>[0-9]+)/$', views.rud_lc, name='rud_lc'),

]
