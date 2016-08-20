# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.conf import settings
from django.views.generic import ListView
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .models import Topic, Node, Post, Notification, ForumAvatar
from .forms import TopicForm, TopicEditForm, AppendixForm, ForumAvatarForm, ReplyForm
from .misc import get_query
import re

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
User = get_user_model()


def get_default_ordering():
    return getattr(
        settings,
        "NIJI_DEFAULT_TOPIC_ORDERING",
        "-last_replied"
    )


def get_topic_ordering(request):
    query_order = request.GET.get("order", "")
    if query_order in ["-last_replied", "last_replied", "pub_date", "-pub_date"]:
        return query_order
    return get_default_ordering()


# Create your views here.
class Index(ListView):
    model = Topic
    paginate_by = 30
    template_name = 'niji/index.html'
    context_object_name = 'topics'

    def get_queryset(self):
        return Topic.objects.visible().select_related(
            'user', 'node'
        ).prefetch_related(
            'user__forum_avatar'
        ).order_by(
            *['order', get_topic_ordering(self.request)]
        )

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['panel_title'] = _('New Topics')
        context['title'] = _('Index')
        context['show_order'] = True
        return context


class NodeView(ListView):
    model = Topic
    paginate_by = 30
    template_name = 'niji/node.html'
    context_object_name = 'topics'

    def get_queryset(self):
        return Topic.objects.visible().filter(
            node__id=self.kwargs.get('pk')
        ).select_related(
            'user', 'node'
        ).prefetch_related(
            'user__forum_avatar'
        ).order_by(
            *['order', get_topic_ordering(self.request)]
        )

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['node'] = node = Node.objects.get(pk=self.kwargs.get('pk'))
        context['title'] = context['panel_title'] = node.title
        context['show_order'] = True
        return context


class TopicView(ListView):
    model = Post
    paginate_by = 30
    template_name = 'niji/topic.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.visible().filter(
            topic_id=self.kwargs.get('pk')
        ).select_related(
            'user'
        ).prefetch_related(
            'user__forum_avatar'
        ).order_by('pub_date')

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        current = Topic.objects.visible().get(pk=self.kwargs.get('pk'))
        current.increase_view_count()
        context['topic'] = current
        context['title'] = context['topic'].title
        context['node'] = context['topic'].node
        context['form'] = ReplyForm()
        return context

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        current = Topic.objects.visible().get(pk=self.kwargs.get('pk'))
        if current.closed:
            return HttpResponseForbidden("Topic closed")
        topic_id = self.kwargs.get('pk')
        form = ReplyForm(
            request.POST,
            user=request.user,
            topic_id=topic_id
        )
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse('niji:topic', kwargs={'pk': topic_id})
            )


def user_info(request, pk):
    u = User.objects.get(pk=pk)
    return render(request, 'niji/user_info.html', {
        'title': u.username,
        'user': u,
        'topics': u.topics.visible().select_related('node')[:10],
        'replies': u.posts.visible().select_related('topic', 'user').order_by('-pub_date')[:30],
    })


class UserTopics(ListView):
    model = Post
    paginate_by = 30
    template_name = 'niji/user_topics.html'
    context_object_name = 'topics'

    def get_queryset(self):
        return Topic.objects.visible().filter(
            user_id=self.kwargs.get('pk')
        ).select_related(
            'user', 'node'
        ).prefetch_related(
            'user__forum_avatar'
        )

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['user'] = User.objects.get(pk=self.kwargs.get('pk'))
        context['panel_title'] = context['title'] = context['user'].username
        return context


class SearchView(ListView):
    model = Topic
    paginate_by = 30
    template_name = 'niji/search.html'
    context_object_name = 'topics'

    def get_queryset(self):
        keywords = self.kwargs.get('keyword')
        query = get_query(keywords, ['title'])
        return Topic.objects.visible().filter(
            query
        ).select_related(
            'user', 'node'
        ).prefetch_related(
            'user__forum_avatar'
        ).order_by(
            get_topic_ordering(self.request)
        )

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['title'] = context['panel_title'] = _('Search: ') + self.kwargs.get('keyword')
        context['show_order'] = True
        return context


def search_redirect(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        return HttpResponseRedirect(reverse('niji:search', kwargs={'keyword': keyword}))
    else:
        return HttpResponseForbidden('Post you cannot')


@login_required
def create_topic(request):
    if request.method == 'POST':
        form = TopicForm(request.POST, user=request.user)
        if form.is_valid():
            t = form.save()
            return HttpResponseRedirect(reverse('niji:topic', kwargs={'pk': t.pk}))
    else:
        form = TopicForm()

    return render(request, 'niji/create_topic.html', {'form': form, 'title': _('Create Topic')})


@login_required
def edit_topic(request, pk):
    topic = Topic.objects.get(pk=pk)
    if topic.reply_count > 0:
        return HttpResponseForbidden(_('Editing is not allowed when topic has been replied'))
    if not topic.user == request.user:
        return HttpResponseForbidden(_('You are not allowed to edit other\'s topic'))
    if request.method == 'POST':
        form = TopicEditForm(request.POST, instance=topic)
        if form.is_valid():
            t = form.save()
            return HttpResponseRedirect(reverse('niji:topic', kwargs={'pk': t.pk}))
    else:
        form = TopicEditForm(instance=topic)

    return render(request, 'niji/edit_topic.html', {'form': form, 'title': _('Edit Topic')})


@login_required
def create_appendix(request, pk):
    topic = Topic.objects.get(pk=pk)
    if not topic.user == request.user:
        return HttpResponseForbidden(_('You are not allowed to append other\'s topic'))
    if request.method == 'POST':
        form = AppendixForm(request.POST, topic=topic)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('niji:topic', kwargs={'pk': topic.pk}))
    else:
        form = AppendixForm()

    return render(request, 'niji/create_appendix.html', {
        'form': form, 'title': _('Create Appendix'), 'pk': pk
    })


@login_required
def upload_avatar(request):
    avatar = ForumAvatar.objects.filter(user_id=request.user.id).first()
    if request.method == 'POST':
        if avatar:
            form = ForumAvatarForm(request.POST, request.FILES, instance=avatar, user=request.user)
        else:
            form = ForumAvatarForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('niji:index'))
    else:
        if avatar:
            form = ForumAvatarForm(instance=request.user.forum_avatar)
        else:
            form = ForumAvatarForm()

    return render(request, 'niji/upload_avatar.html', {'form': form, 'title': _('Upload Avatar')})


@login_required
def notification_view(request):
    notifications = request.user.received_notifications.all().order_by('-pub_date')
    Notification.objects.filter(to=request.user).update(read=True)
    return render(request, 'niji/notifications.html', {
        'title': _("Notifications"),
        'notifications': notifications,
    })


class NotificationView(ListView):

    model = Notification
    paginate_by = 30
    template_name = 'niji/notifications.html'
    context_object_name = 'notifications'

    def get_queryset(self):
        Notification.objects.filter(to=self.request.user).update(read=True)
        return Notification.objects.filter(
            to=self.request.user
        ).select_related(
            'sender', 'topic', 'post'
        ).prefetch_related(
            'sender__forum_avatar', 'post__topic'
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['title'] = _("Notifications")
        return context


def login_view(request):
    if request.method == "GET":
        return render(request, 'niji/login.html', {'title': _("Login")})
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        valid = True
        if not username or not password:
            valid = False
            messages.add_message(request, messages.INFO, _("Username and password cannot be empty"))
        user = User.objects.filter(username=username).first()
        if not user:
            valid = False
            messages.add_message(request, messages.INFO, _("User does not exist"))
        user = authenticate(username=username, password=password)
        if (user is not None) and valid:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('niji:index'))
            else:
                valid = False
                messages.add_message(request, messages.INFO, _("User deactivated"))
        else:
            valid = False
            messages.add_message(request, messages.INFO, _("Incorrect password"))
        if not valid:
            return HttpResponseRedirect(reverse("niji:login"))


def reg_view(request):
    if request.method == "GET":
        return render(request, 'niji/reg.html', {'title': _("Reg")})
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password1")
        password2 = request.POST.get("password2")
        valid = True
        if User.objects.filter(username=username).exists():
            valid = False
            messages.add_message(request, messages.INFO, _("User already exists"))
        if password != password2:
            valid = False
            messages.add_message(request, messages.INFO, _("Password does not match"))
        if not EMAIL_REGEX.match(email):
            valid = False
            messages.add_message(request, messages.INFO, _("Invalid Email"))
        if not valid:
            return HttpResponseRedirect(reverse("niji:reg"))
        else:
            User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            user = authenticate(
                username=username,
                password=password
            )
            login(request, user)
            return HttpResponseRedirect(reverse("niji:index"))


@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("niji:index"))
