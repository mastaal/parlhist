FROM python:3.12-bookworm as base
RUN useradd --system --create-home --home-dir /home/parlhist --user-group --uid 1000 --shell /bin/bash parlhist

WORKDIR /home/parlhist
COPY ./parlhist ./parlhist
COPY ./parlhistnl ./parlhistnl
COPY \
    ./requirements.txt \
    ./manage.py \
    ./initialize_database_handelingen.sh \
    ./initialize_database_kamerstukken.sh \
    ./initialize_database_staatsblad.sh \
    ./LICENSE \
    .
COPY ./container/settings.py ./parlhist/settings.py
RUN pip install --no-cache-dir --requirement /home/parlhist/requirements.txt

EXPOSE 8000
USER 1000
#ENTRYPOINT ["python", "./manage.py"]
CMD ["/bin/bash"]
