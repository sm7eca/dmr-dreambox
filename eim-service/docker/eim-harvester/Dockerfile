FROM python:3.9.1-alpine3.13

COPY ./requirements.txt /.
RUN pip install --no-cache-dir -r /requirements.txt

ENV PYTHON_PATH /app
ENV EIM_HARVESTER_PERIODICITY_SEC 12

COPY ./src /app
WORKDIR /app

ENTRYPOINT ["python3", "main.py"]
