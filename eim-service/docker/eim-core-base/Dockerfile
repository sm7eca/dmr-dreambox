FROM tiangolo/uvicorn-gunicorn:python3.8-alpine3.10

LABEL maintainer="Sebastian Ramirez <tiangolo@gmail.com>"

COPY requirements.txt /

RUN pip install --upgrade --no-cache-dir pip
RUN pip install --no-cache-dir -r /requirements.txt
