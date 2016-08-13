from rest_framework import viewsets
from niji.models import Topic
from niji.serializers import TopicSerializer


class TopicApiView(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
