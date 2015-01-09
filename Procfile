web: gunicorn portal.wsgi --log-file -
worker: celery worker -E -B --app=portal --loglevel=info