#!/bin/bash

export DJANGO_DEBUG=1
export DATABASE_URL="postgres://elsterdev:elsterdev123@localhost/elster_qp"
export SENDGRID_PASSWORD="ignore"
export SENDGRID_USERNAME="elster"
export AWS_S3_ACCESS_KEY_ID="blah_blah"
export AWS_S3_SECRET_ACCESS_KEY=" blah_blah "
export AWS_STORAGE_BUCKET_NAME="elster-qp"
export DJANGO_SITE_ID=1

virtualenv venv
. ./venv/bin/activate
pip install -r ./requirements.txt
python ./manage.py collectstatic --noinput
python ./manage.py validate
python ./manage.py test
deactivate
