# -*- coding: utf-8 -*-
from django.conf.urls import url, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework import routers
from . import api
from . import views

api_router = routers.DefaultRouter()
api_router.register(r'topics', api.TopicApiView)
api_router.register(r'post', api.PostApiView)

urlpatterns = [
    url(r'^page/(?P<page>[0-9]+)/$', views.Index.as_view(), name='index'),
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^n/(?P<pk>\d+)/page/(?P<page>[0-9]+)/$', views.NodeView.as_view(), name='node'),
    url(r'^n/(?P<pk>\d+)/$', views.NodeView.as_view(), name='node'),
    url(r'^t/(?P<pk>\d+)/edit/$', views.edit_topic, name='edit_topic'),
    url(r'^t/(?P<pk>\d+)/append/$', views.create_appendix, name='create_appendix'),
    url(r'^t/(?P<pk>\d+)/page/(?P<page>[0-9]+)/$', views.TopicView.as_view(), name='topic'),
    url(r'^t/(?P<pk>\d+)/$', views.TopicView.as_view(), name='topic'),
    url(r'^u/(?P<pk>\d+)/$', views.user_info, name='user_info'),
    url(r'^u/(?P<pk>\d+)/topics/page/(?P<page>[0-9]+)/$', views.UserTopics.as_view(), name='user_topics'),
    url(r'^u/(?P<pk>\d+)/topics/$', views.UserTopics.as_view(), name='user_topics'),
    url(r'^login/$', views.login_view, name='login'),
    url(r'^reg/$', views.reg_view, name='reg'),
    url(r'^logout/$', views.logout_view, name="logout"),
    url(r'^search/$', views.search_redirect, name='search_redirect'),
    url(r'^search/(?P<keyword>.*?)/page/(?P<page>[0-9]+)/$', views.SearchView.as_view(), name='search'),
    url(r'^search/(?P<keyword>.*?)/$', views.SearchView.as_view(), name='search'),
    url(r'^t/create/$', views.create_topic, name='create_topic'),
    url(r'^notifications/$', views.NotificationView.as_view(), name='notifications'),
    url(r'^avatar/$', views.upload_avatar, name="upload_avatar"),
    url(r'^api/', include(api_router.urls)),
]
