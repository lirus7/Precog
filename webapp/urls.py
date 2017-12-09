from django.conf.urls import url
from . import views

urlpatterns=[
url(r'^$',views.index),
url(r'^type',views.view_type),
url(r'^favcount',views.view_favcount),
url(r'^tweetretweet',views.view_tweetretweet),
url(r'^hashtags',views.view_hashtags),
url(r'^location',views.view_location),
url(r'^network_delhi',views.view_network_delhi),
url(r'^network_mumbai',views.view_network_mumbai),
url(r'^nonusers',views.view_non_users),
url(r'^location',views.view_location)
]
