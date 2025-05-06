# Based on the example from: https://www.docker.com/blog/how-to-dockerize-django-app/
FROM python:3.12-bookworm AS builder

# Note the .containerignore file at the repository root to prevent irrelevant files to be added to the container
RUN mkdir /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

COPY requirements.txt /app/

RUN pip install --no-cache-dir --requirement /app/requirements.txt

FROM python:3.12-slim AS base

RUN useradd --system --create-home --home-dir /app --user-group --uid 1000 --shell /bin/bash parlhist

COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

LABEL org.opencontainers.image.licenses="EUPL-1.2"
LABEL org.opencontainers.image.author="Martijn Staal <parlhist [at] martijn-staal.nl>"
LABEL org.opencontainers.image.source="https://github.com/mastaal/parlhist"
LABEL org.opencontainers.image.base.name="parlhist"
LABEL org.opencontainers.image.title="parlhist"

WORKDIR /app
COPY --chown=parlhist:parlhist . /app/
COPY ./container/settings.py ./parlhist/settings.py

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN mkdir /data && chown 1000 /data
VOLUME [ "/data" ]

EXPOSE 8000
USER parlhist
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "parlhist.wsgi:application"]