from rest_framework import serializers
from niji.models import Topic, Post


class TopicSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Topic
        fields = ('title', 'content_raw', 'order', 'hidden', 'closed')


class PostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Post
        fields = ('content_raw', 'hidden')
