from django.contrib import admin
from .models import Topic, Node, Post

# Register your models here.


class PostInline(admin.TabularInline):
    model = Post
    fields = ('user', 'content_raw')


class TopicAdmin(admin.ModelAdmin):
    inlines = [
        PostInline
    ]

admin.site.register(Topic, TopicAdmin)
admin.site.register(Node)
