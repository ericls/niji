# -*- coding: utf-8 -*-
from .models import Node
from django.utils.translation import ugettext as _
from django.conf import settings


def niji_processor(request):
    nodes = Node.objects.all()
    site_name = _(getattr(settings, 'NIJI_SITE_NAME', ''))
    niji_login_url_name = getattr(settings, 'NIJI_LOGIN_URL_NAME', 'niji:login')
    niji_reg_url_name = getattr(settings, 'NIJI_REG_URL_NAME', 'niji:reg')
    try:
        unread_count = request.user.received_notifications.filter(read=False).count()
    except AttributeError:
        unread_count = None
    return {
        'nodes': nodes,
        'unread_count': unread_count,
        'site_name': site_name,
        'niji_login_url_name': niji_login_url_name,
        'niji_reg_url_name': niji_reg_url_name
    }
