# -*- coding: utf-8 -*-
from .models import Node
from django.utils.translation import ugettext as _
from django.conf import settings


def niji_processor(request):
    nodes = Node.objects.all()
    site_name = _(getattr(settings, 'NIJI_SITE_NAME', ''))
    try:
        unread_count = request.user.received_notifications.filter(read=False).count()
    except AttributeError:
        unread_count = None
    return {'nodes': nodes, 'unread_count': unread_count, 'site_name': site_name}
