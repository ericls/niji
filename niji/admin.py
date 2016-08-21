# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Topic, Node, Post, Appendix


class PostInline(admin.TabularInline):
    model = Post
    raw_id_fields = (
        'user',
    )
    fields = (
        'user',
        'content_raw',
        'hidden',
    )
    extra = 1


class AppendixInline(admin.TabularInline):
    model = Appendix
    fields = (
        'content_raw',
    )
    extra = 1


class TopicAdmin(admin.ModelAdmin):

    def is_top_topic(self, obj):
        return obj.order < 10

    is_top_topic.boolean = True

    list_display = (
        'title',
        'user',
        'pub_date',
        'last_replied',
        'view_count',
        'reply_count',
        'hidden',
        'closed',
        'is_top_topic',
    )
    fields = (
        'user',
        'title',
        'content_raw',
        'hidden',
        'closed'
    )

    search_fields = (
        'title',
        'user__username',
        'user__email'
    )
    raw_id_fields = (
        'user',
    )
    inlines = [
        PostInline,
        AppendixInline
    ]


class NodeAdmin(admin.ModelAdmin):

    def number_of_topics(self, obj):
        topics = Topic.objects.filter(node=obj)
        return "{}({})".format(topics.count(), topics.visible().count())

    number_of_topics.short_description = "Number of Topics [total(visible)]"

    list_display = (
        'title',
        'number_of_topics'
    )
    search_fields = (
        'title',
    )

admin.site.register(Topic, TopicAdmin)
admin.site.register(Node, NodeAdmin)
