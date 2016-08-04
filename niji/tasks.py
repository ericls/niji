# -*- coding: utf-8 -*-
from __future__ import absolute_import
from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model


logger = get_task_logger(__name__)


@shared_task
def notify(sender, to, topic=None, post=None):
    from niji.models import Notification, Topic, Post
    User = get_user_model()

    if not any([topic, post]):
        logger.warning('No topic or post provided, ignored')

    ntf, created = Notification.objects.get_or_create(
        topic=Topic.objects.filter(pk=topic).first(),
        post=Post.objects.filter(pk=post).first(),
        sender=User.objects.get(username=sender),
        to=User.objects.get(username=to)
    )
    if created:
        logger.info('Successfully created notification from {0.sender.username} to {0.to.username}'.format(ntf))
    else:
        logger.info('Ignored duplicated notification from {0.sender.username} to {0.to.username}'.format(ntf))
    return True
