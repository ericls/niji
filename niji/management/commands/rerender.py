from django.core.management.base import BaseCommand, CommandError
from niji.models import Topic, Post, render_content
import logging
import sys


class Command(BaseCommand):
    help = "Re-render topics and posts"

    def add_arguments(self, parser):
        parser.add_argument('--all', action="store_true")
        parser.add_argument('--topics', action="store", nargs="+", default=[])
        parser.add_argument('--posts', action="store", nargs="+", default=[])

    def handle(self, *args, **options):
        for_all = options['all']
        topic_ids = options['topics']
        post_ids = options['posts']

        if (not for_all) and (not topic_ids) and (not post_ids):
            self.stdout.write(self.style.ERROR("At least one of '--all', '--topics', '--posts' is required"))
            return

        if not for_all:
            topics = Topic.objects.filter(pk__in=topic_ids).select_related('user')
            posts = Post.objects.filter(pk__in=post_ids).select_related('user')
        else:
            topics = Topic.objects.select_related('user').all()
            posts = Post.objects.select_related('user').all()

        for topic in topics:
            topic.content_rendered, _ = render_content(topic.content_raw, topic.user.username)
            topic.save()
            self.stdout.write(self.style.SUCCESS('Re-rendered topic {0.id}: {0.title}'.format(topic)))

        for post in posts:
            post.content_rendered, _ = render_content(post.content_raw, post.user.username)
            post.save()
            self.stdout.write(self.style.SUCCESS('Re-rendered post {0.id}, in topic {0.topic.id}: {0.topic.title}'.format(post)))
