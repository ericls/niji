from django.conf.urls import url, include
from niji import urls as niji_urls

urlpatterns = [
    url(r'testurl', include(niji_urls, namespace="niji")),
]
