import os
from django.conf import settings
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yummy_yagi.settings")

app = Celery(
    "yummy_yagi",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["user.tasks"],
)

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.update(
    result_expires=settings.CELERY_RESULT_EXPIRES,
)

if __name__ == "__main__":
    app.start()

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
