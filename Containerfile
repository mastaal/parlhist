FROM python:3.12-bookworm as base

RUN useradd --system --create-home --home-dir /home/parlhist --user-group --uid 1000 --shell /bin/bash parlhist

# Note the .containerignore file at the repository root to prevent irrelevant files to be added to the container
COPY . /home/parlhist
RUN pip install --no-cache-dir --requirement /home/parlhist/requirements.txt

LABEL org.opencontainers.image.licenses="EUPL-1.2"
LABEL org.opencontainers.image.author="Martijn Staal <parlhist [at] martijn-staal.nl>"
LABEL org.opencontainers.image.source="https://github.com/mastaal/parlhist"
LABEL org.opencontainers.image.base.name="parlhist"
LABEL org.opencontainers.image.title="parlhist"

WORKDIR /home/parlhist
COPY ./container/settings.py ./parlhist/settings.py

RUN mkdir /data && chown 1000 /data
VOLUME [ "/data" ]

EXPOSE 8000
USER 1000
ENTRYPOINT ["python", "./manage.py"]
CMD ["runserver", "0.0.0.0:8000"]