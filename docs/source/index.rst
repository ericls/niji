Django-Niji
===========

       Django-NIJI is a pluggable forum APP for Django projects

Demo
----
https://demo.nijiforum.com/

Installation
------------

Requirements
~~~~~~~~~~~~

Django-NIJI is tested with the following Django and Python versions

::

    Django from 1.8 to 1.10
    Python from 2.7 3.4 3.5

Get the package
~~~~~~~~~~~~~~~

Django-NIJI is available on pypi, so just run

::

    pip install django-niji

Configuration
~~~~~~~~~~~~~

Tweak project settings
^^^^^^^^^^^^^^^^^^^^^^

Required Settings:

.. code:: python

    INSTALLED_APPS += [
        'django.contrib.humanize',
        'crispy_forms',
        'niji',
        'rest_framework',
    ]

    # Template context_processors
    TEMPLATES[0]['OPTIONS']['context_processors'].append("niji.context_processors.niji_processor")

    # Media related settings are required for avatar uploading to function properly
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    MEDIA_URL = '/media/'

Other Settings:

.. code:: python

    # Form UI Settings
    CRISPY_TEMPLATE_PACK = 'bootstrap3'

    # Configure where to link to from the Login and Reg buttons in the forum
    NIJI_LOGIN_URL_NAME = "account:login"
    NIJI_REG_URL_NAME = "account:reg"

    # Site Name
    NIJI_SITE_NAME = "A lovely forum"

Configure URLs
^^^^^^^^^^^^^^

Simply include the urls

.. code:: python

    from django.conf.urls import url, include
    from niji import urls as niji_urls

    urlpatterns = [
        ...
        url(r'', include(niji_urls, namespace="niji")),
    ]

Configure Celery
^^^^^^^^^^^^^^^^

Django-NIJI requires celery to send notifications.

**If you already have a celery configured for you Django project, you can use just that.**

Otherwise, follow these simple steps:

Create ``celery.py`` inside project directory
'''''''''''''''''''''''''''''''''''''''''''''

**Please replace ``project_name`` with your project's name**

.. code:: python

    from __future__ import absolute_import

    import os
    from celery import Celery
    from django.conf import settings

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_name.settings') # Change this to the project name

    app = Celery('project_name')

    app.config_from_object('django.conf:settings')
    app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

Modify project ``__init__.py``
''''''''''''''''''''''''''''''

.. code:: python

    from __future__ import absolute_import
    from .celery import app as celery_app

Add setting entries
'''''''''''''''''''

**Please adjust some of the settings according to your case**

.. code:: python

    BROKER_URL = 'redis://localhost:6379/0'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'

If you don't want to run a celery worker separately, include these
entries:

.. code:: python

    BROKER_BACKEND = 'memory'
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    CELERY_ALWAYS_EAGER = True

Otherwise, you'll need to run ``celery -A project_name worker -l INFO``

Configure Editor (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have ``pagedown`` in your ``settings.py``, Django-NIJI will
enable that editor automatically.

In order not to break the layout you may need to include the following
settings:

.. code:: python

    # Pagedown Editor
    PAGEDOWN_WIDGET_CSS = ('pagedown/demo/browser/demo.css', "css/editor.css",)
    PAGEDOWN_WIDGET_TEMPLATE = 'niji/widgets/pagedown.html'

Migrate
~~~~~~~

::

    python manage.py migrate

Collect Static Assets
~~~~~~~~~~~~~~~~~~~~~

::

    python manage.py collectstatic



Now, login to your project's admin page and add some Nodes before you can post anything.
