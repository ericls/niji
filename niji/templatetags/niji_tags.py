from django import template
from django.utils.html import escape
from django.contrib.auth.models import User
from six.moves.urllib.parse import urlencode, urlparse, parse_qs
from django.core.urlresolvers import reverse
from niji.models import ForumAvatar
import hashlib

register = template.Library()


@register.simple_tag
def gravatar_url(user, size=48):
    if isinstance(user, User):
        email = user.email
    else:
        email = user

    default = ""

    avatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(
        email.lower().encode('utf-8')
    ).hexdigest() + "?"
    avatar_url += urlencode({'d': default, 's': str(size)})

    return escape(avatar_url)


@register.simple_tag
def avatar_url(user, size=48, no_gravatar=False):
    try:
        avatar = user.forum_avatar
    except ForumAvatar.DoesNotExist:
        return gravatar_url(user, size)
    else:
        if avatar.use_gravatar and not no_gravatar or not avatar.image:
            return gravatar_url(user, size)
        else:
            return avatar.image.url


@register.simple_tag
def change_url(request, kwargs=None, query=None):
    kwargs = kwargs or {}
    query = query or {}
    rm = request.resolver_match
    _kwargs = rm.kwargs.copy()
    _kwargs.update(kwargs)
    if _kwargs.get("page") == 1:
        _kwargs.pop('page', None)
    qs = parse_qs(urlparse(request.get_full_path()).query)
    qs.update(query)
    path = reverse(
        '%s:%s' % (rm.namespace, rm.url_name),
        args=rm.args,
        kwargs=_kwargs,
    )
    if (qs):
        return "%s?%s" % (path, urlencode(qs, True))
    else:
        return path


@register.simple_tag
def change_page(request, page=1):
    return change_url(request, {"page": page})


@register.simple_tag
def change_topic_ordering(request, ordering):
    return change_url(request, None, {"order": ordering})


@register.inclusion_tag('niji/includes/pagination.html', takes_context=True)
def get_pagination(context, first_last_amount=2, before_after_amount=4):
    page_obj = context['page_obj']
    paginator = context['paginator']
    is_paginated = context['is_paginated']
    page_numbers = []

    # Pages before current page
    if page_obj.number > first_last_amount + before_after_amount:
        for i in range(1, first_last_amount + 1):
            page_numbers.append(i)

        if first_last_amount + before_after_amount + 1 != paginator.num_pages:
            page_numbers.append(None)

        for i in range(page_obj.number - before_after_amount, page_obj.number):
            page_numbers.append(i)

    else:
        for i in range(1, page_obj.number):
            page_numbers.append(i)

    # Current page and pages after current page
    if page_obj.number + first_last_amount + before_after_amount < paginator.num_pages:
        for i in range(page_obj.number, page_obj.number + before_after_amount + 1):
            page_numbers.append(i)

        page_numbers.append(None)

        for i in range(paginator.num_pages - first_last_amount + 1, paginator.num_pages + 1):
            page_numbers.append(i)

    else:
        for i in range(page_obj.number, paginator.num_pages + 1):
            page_numbers.append(i)

    return {
        'paginator': paginator,
        'page_obj': page_obj,
        'page_numbers': page_numbers,
        'is_paginated': is_paginated,
        'request': context['request'],
    }
