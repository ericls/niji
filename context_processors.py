# -*- coding: utf-8 -*-
from .models import Node


def niji_processor(request):
    nodes = Node.objects.all()
    try:
        unread_count = request.user.received_notifications.filter(read=False).count()
    except AttributeError:
        unread_count = None
    return {'nodes': nodes, 'unread_count': unread_count}
