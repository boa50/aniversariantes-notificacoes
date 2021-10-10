#!/bin/bash
docker run --rm -v "${PWD}":/home boa50/notificacoes python /home/cronjob.py
