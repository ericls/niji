#NIJI

> NIJI is a forum APP for Django projects.
> NIJI can be integrated into existing Django projects.

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