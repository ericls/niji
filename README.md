#NIJI

[![Build Status](https://travis-ci.org/ericls/niji.svg?branch=master)](https://travis-ci.org/ericls/niji)

> NIJI is a forum APP for Django projects.
>
> NIJI is developed with the idea that it should be easily integrated into existing Django projects

## Quick Installation (Integration)

### Install dependencies

```
pip install -r requirements.txt
```

### Modify settings.py

```
# CELERY SETTINGS

BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


# Template context_processors
TEMPLATES[0]['OPTIONS']['context_processors'].append("niji.context_processors.niji_processor")


# Form UI Settings
CRISPY_TEMPLATE_PACK = 'bootstrap3'


INSTALLED_APPS = [
    ....
    'django.contrib.humanize',
    'crispy_forms',
    'niji',
]
```

### Include urls to project's `urls.py`

```
from django.conf.urls import url, include
from niji import urls as niji_urls

urlpatterns = [
    ...
    url(r'', include(niji_urls, namespace="niji")),
]
```

### Create `celery.py` inside project directory

```
from __future__ import absolute_import

import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_name.settings') # Change this to the project name

app = Celery('project_name')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
```

### Modify project `__init__.py`

```
from __future__ import absolute_import
from .celery import app as celery_app
```


### Start celery worker

```
celery -A project_name worker -l INFO
```

## Other Settings

### Use different login and reg views.

By default, the login and reg views are `niji:login` and `niji:reg`, however those views are not well tested and many Django sites have their own account system. The following settings can be used to override the login and reg views. Suppose your urls to login and reg views are named `account:login` and `account:reg` respectively.

```
NIJI_LOGIN_URL_NAME = "account:login"
NIJI_REG_URL_NAME = "account:reg"
```

### Use markdown editor with preview (django-pagedown)

Django-pagedown editor is automatically enabled if you have `pagedown` in your `INSTALLED_APPS`

In order not to break the layout and add an i18n tweak to the text "Preview", you'll need to include the following settings:

```
# Pagedown Editor
PAGEDOWN_WIDGET_CSS = ('pagedown/demo/browser/demo.css', "css/editor.css",)
PAGEDOWN_WIDGET_TEMPLATE = 'niji/widgets/pagedown.html'
```

### Show site name in html title

```
NIJI_SITE_NAME = "xxx"  # This will add "-xxx" to html title
```

### Run without starting a celery worker

Add the following to your settings

```
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_ALWAYS_EAGER = True
BROKER_BACKEND = 'memory'
```

With these settings present, you don't need to run a separate celery worker.

And the tasks will be executed in a synchronous manner.

## Management Commands

### Re-render
```
Re-render topics and posts
usage: manage.py rerender [-h] [--version] [-v {0,1,2,3}]
                          [--settings SETTINGS] [--pythonpath PYTHONPATH]
                          [--traceback] [--no-color] [--all]
                          [--topics TOPICS [TOPICS ...]]
                          [--posts POSTS [POSTS ...]]

```
#### Examples
```
python manage.py rerender --topics 1 2 3
# rerenders topics whose pks are in [1, 2, 3]
python manage.py rerender --posts 1 2 3
# rerenders posts whose pks are in [1, 2, 3]
python manage.py rerender --all
# rerenders all topics and posts
```
