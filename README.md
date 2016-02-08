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
    'crispy_forms',
    'niji',
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