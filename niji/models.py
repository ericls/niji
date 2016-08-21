# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import F
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.urlresolvers import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _
from functools import partial
from niji.tasks import notify
from PIL import Image
from io import BytesIO
import xxhash
import mistune
import re
import six
if six.PY2:
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')


MENTION_REGEX = re.compile(r'@(\S+)', re.M)
USER_MODEL = settings.AUTH_USER_MODEL


def _replace_username(link, matchobj):
    return "@<a href=\"{link}\">{username}</a>{whitespace}".format(
        username=matchobj.group("username")[1:],
        whitespace=matchobj.group("whitespace"),
        link=link
    )


def render_content(content_raw, sender):
    """
    :param content_raw: Raw content
    :param sender: user as username
    :return: (rendered_content, mentioned_user_list)
    """
    content_rendered = mistune.markdown(content_raw)
    mentioned = list(set(re.findall(MENTION_REGEX, content_raw)))
    mentioned = [x for x in mentioned if x != sender]
    mentioned_users = get_user_model().objects.filter(username__in=mentioned)
    for user in mentioned_users:
        content_rendered = re.sub(
            r'(?P<username>@%s)(?P<whitespace>\s|<\/p>)' % user.username,
            partial(_replace_username, reverse('niji:user_info', kwargs={"pk": user.pk})),
            content_rendered,
            re.M
        )
    return content_rendered, mentioned_users


class TopicQueryset(models.QuerySet):

    def visible(self):
        return self.filter(hidden=False)


@python_2_unicode_compatible
class Topic(models.Model):
    user = models.ForeignKey(USER_MODEL, related_name='topics', verbose_name=_("user"))
    title = models.CharField(max_length=120, verbose_name=_("title"))
    content_raw = models.TextField(verbose_name=_("raw content"))
    content_rendered = models.TextField(default='', blank=True, verbose_name=_("rendered content"))
    view_count = models.IntegerField(default=0, verbose_name=_("view count"))
    reply_count = models.IntegerField(default=0, verbose_name=_("reply count"))
    node = models.ForeignKey('Node', related_name='topics', verbose_name=_("node"))
    pub_date = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("published time"))
    last_replied = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("last replied time"))
    order = models.IntegerField(default=10, verbose_name=_("order"))
    hidden = models.BooleanField(default=False, verbose_name=_("hidden"))
    closed = models.BooleanField(default=False, verbose_name=_("closed"))
    objects = TopicQueryset.as_manager()

    raw_content_hash = None

    def __init__(self, *args, **kwargs):
        super(Topic, self).__init__(*args, **kwargs)
        self.raw_content_hash = xxhash.xxh64(self.content_raw).hexdigest()

    def get_reply_count(self):
        return self.replies.visible().count()

    def get_last_replied(self):
        last_visible_reply = self.replies.visible().order_by('-pub_date').first()
        if last_visible_reply:
            return last_visible_reply.pub_date
        return self.pub_date

    def increase_view_count(self):
        Topic.objects.filter(pk=self.id).update(view_count=F('view_count') + 1)

    def save(self, *args, **kwargs):
        new_hash = xxhash.xxh64(self.content_raw).hexdigest()
        mentioned_users = []
        if new_hash != self.raw_content_hash or (not self.pk):
            # To (re-)render the content if content changed or topic is newly created
            self.content_rendered, mentioned_users = render_content(self.content_raw, sender=self.user.username)
        super(Topic, self).save(*args, **kwargs)
        self.raw_content_hash = new_hash
        for to in mentioned_users:
                notify.delay(to=to.username, sender=self.user.username, topic=self.pk)

    class Meta:
        ordering = ['order', '-pub_date']

    def __str__(self):
        return self.title


class PostQueryset(models.QuerySet):

    use_for_related_fields = True

    def visible(self):
        return self.filter(hidden=False)


@python_2_unicode_compatible
class Post(models.Model):
    topic = models.ForeignKey('Topic', related_name='replies', verbose_name=_("topic"))
    user = models.ForeignKey(USER_MODEL, related_name='posts', verbose_name=_("user"))
    content_raw = models.TextField(verbose_name=_("raw content"))
    content_rendered = models.TextField(default='', verbose_name=_("rendered content"))
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name=_("published time"))
    hidden = models.BooleanField(default=False, verbose_name=_("hidden"))
    objects = PostQueryset.as_manager()

    raw_content_hash = None

    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)
        self.raw_content_hash = xxhash.xxh64(self.content_raw).hexdigest()

    def __str__(self):
        return 'Reply to %s' % self.topic.title

    def save(self, *args, **kwargs):
        new_hash = xxhash.xxh64(self.content_raw).hexdigest()
        mentioned_users = []
        if new_hash != self.raw_content_hash or (not self.pk):
            self.content_rendered, mentioned_users = render_content(self.content_raw, sender=self.user.username)
        super(Post, self).save(*args, **kwargs)
        t = self.topic
        t.reply_count = t.get_reply_count()
        t.last_replied = t.get_last_replied()
        t.save(update_fields=['last_replied', 'reply_count'])
        for to in mentioned_users:
            notify.delay(to=to.username, sender=self.user.username, post=self.pk)

    def delete(self, *args, **kwargs):
        super(Post, self).delete(*args, **kwargs)
        t = self.topic
        t.reply_count = t.get_reply_count()
        t.last_replied = t.get_last_replied()
        t.save(update_fields=['last_replied', 'reply_count'])


@python_2_unicode_compatible
class Notification(models.Model):
    sender = models.ForeignKey(USER_MODEL, related_name='sent_notifications', verbose_name=_("sender"))
    to = models.ForeignKey(USER_MODEL, related_name='received_notifications', verbose_name=_("recipient"))
    topic = models.ForeignKey('Topic', null=True, verbose_name=_("topic"))
    post = models.ForeignKey('Post', null=True, verbose_name=_("reply"))
    read = models.BooleanField(default=False, verbose_name=_("read"))
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name=_("published time"))

    def __str__(self):
        return 'Notification from %s to %s' % (self.sender.username, self.to.username)


@python_2_unicode_compatible
class Appendix(models.Model):
    topic = models.ForeignKey('Topic', verbose_name=_("topic"))
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name=_("published time"))
    content_raw = models.TextField(verbose_name=_("raw content"))
    content_rendered = models.TextField(default='', blank=True, verbose_name=_("rendered content"))

    raw_content_hash = None

    def __init__(self, *args, **kwargs):
        super(Appendix, self).__init__(*args, **kwargs)
        self.raw_content_hash = xxhash.xxh64(self.content_raw).hexdigest()

    def save(self, *args, **kwargs):
        new_hash = xxhash.xxh64(self.content_raw).hexdigest()
        if new_hash != self.raw_content_hash or (not self.pk):
            self.content_rendered = mistune.markdown(self.content_raw)
        super(Appendix, self).save(*args, **kwargs)
        self.raw_content_hash = new_hash

    def __str__(self):
        return 'Appendix to %s' % self.topic.title


@python_2_unicode_compatible
class Node(models.Model):
    title = models.CharField(max_length=30, verbose_name=_("title"))
    description = models.TextField(default='', blank=True, verbose_name=_("description"))

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class NodeGroup(models.Model):
    title = models.CharField(max_length=30)
    node = models.ManyToManyField('Node')

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class ForumAvatar(models.Model):
    user = models.OneToOneField(USER_MODEL, related_name='forum_avatar')
    use_gravatar = models.BooleanField(default=False)
    image = models.ImageField(max_length=255,
                              upload_to='uploads/forum/avatars/',
                              blank=True,
                              default="",
                              null=True)

    def save(self, *args, **kwargs):
        existing_avatar = ForumAvatar.objects.filter(user=self.user).first()
        if existing_avatar:
            self.id = existing_avatar.id
        if not self.image:
            self.use_gravatar = True
        else:
            i = Image.open(self.image)
            i.thumbnail((120, 120), Image.ANTIALIAS)
            i_io = BytesIO()
            i.save(i_io, format='PNG')
            self.image = InMemoryUploadedFile(
                i_io, None, '%s.png' % self.user_id, 'image/png', None, None
            )
        print(self.image)
        super(ForumAvatar, self).save(*args, **kwargs)

    def __str__(self):
        return "Avatar for user: %s" % self.user.username
