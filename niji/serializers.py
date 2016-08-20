from rest_framework import serializers
from niji.models import Topic


class TopicSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Topic
        fields = ('title', 'content_raw', 'order', 'hidden', 'closed')
