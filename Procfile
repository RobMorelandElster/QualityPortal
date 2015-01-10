web: gunicorn portal.wsgi --log-file -
worker: celery worker -E --app=portal --loglevel=INFO