import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from django.test.utils import get_runner
from django.conf import settings

import django
django.setup()

from celery import Celery
app = Celery('project_name')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


def runtests():
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True)
    failures = test_runner.run_tests(['niji'])
    sys.exit(bool(failures))


if __name__ == "__main__":
    runtests()
