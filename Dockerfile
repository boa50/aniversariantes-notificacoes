FROM python:3.8.5-alpine3.12
LABEL maintainer="https://github.com/boa50"

WORKDIR /usr/src

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
