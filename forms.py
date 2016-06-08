# -*- coding: utf-8 -*-
from django.forms import ModelForm
from crispy_forms.layout import Submit
from crispy_forms.helper import FormHelper
from .models import Topic, Appendix, ForumAvatar
from django.utils.translation import ugettext as _


class TopicForm(ModelForm):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(TopicForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Submit')))

    class Meta:
        model = Topic
        fields = ['node', 'title', 'content_raw']
        labels = {
            'content_raw': _('Content'),
            'node': _('Node'),
            'title': _('Title'),
        }

    def save(self, commit=True):
        inst = super(TopicForm, self).save(commit=False)
        inst.user = self.user
        if commit:
            inst.save()
            self.save_m2m()
        return inst


class TopicEditForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(TopicEditForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Submit')))

    class Meta:
        model = Topic
        fields = ('content_raw', )
        labels = {
            'content_raw': _('Content'),
        }


class AppendixForm(ModelForm):

    def __init__(self, *args, **kwargs):
        self.topic = kwargs.pop('topic', None)
        super(AppendixForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Submit')))

    class Meta:
        model = Appendix
        fields = ('content_raw', )
        labels = {
            'content_raw': _('Content'),
        }

    def save(self, commit=True):
        inst = super(AppendixForm, self).save(commit=False)
        inst.topic = self.topic
        if commit:
            inst.save()
            self.save_m2m()
        return inst


class ForumAvatarForm(ModelForm):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ForumAvatarForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Submit')))

    class Meta:
        model = ForumAvatar
        fields = ('image', 'use_gravatar')
        labels = {
            'image': _('Avatar Image'),
            'use_gravatar': _("Always Use Gravatar")
        }

    def save(self, commit=True):
        inst = super(ForumAvatarForm, self).save(commit=False)
        inst.user = self.user
        if commit:
            inst.save()
            self.save_m2m()
        return inst
