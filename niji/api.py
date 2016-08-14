from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from niji.models import Topic
from niji.serializers import TopicSerializer


class SessionAuthenticationExemptCSRF(SessionAuthentication):

    def enforce_csrf(self, request):
        return


class TopicApiView(viewsets.ModelViewSet):
    authentication_classes = (SessionAuthenticationExemptCSRF,)
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
