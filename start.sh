#!/bin/bash
flask --app index --debug run && celery -A index.celery worker --loglevel=info
