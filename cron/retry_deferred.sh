#!/bin/sh
WORKON_HOME=/home/pouch/env
PROJECT_ROOT=/home/pouch/pouch
. $WORKON_HOME/bin/activate
cd $PROJECT_ROOT
python manage.py retry_deferred >> $PROJECT_ROOT/logs/cron_retry.log 2>&1
