# Developing parlhist

Some notes and tips for developing parlhist

## Installing development tools

Using the python virtual environment manager of your choice, install all packages in development_requirements.txt to get all development tools.

## Working with celery

### Running rabbitmq

Rabbitmq is the recommended task queue for celery. You can run a local instance using:

```
$ podman run -it --rm --name rabbitmq -p 5672:5672 docker.io/rabbitmq
```

(If you use docker, just change 'podman' into 'docker')

### Starting a celery working
Boot up a celery worker to start executing enqueued tasks:

```
$ celery -A parlhist worker -l INFO
```

### Running flower

"[Flower](https://flower.readthedocs.io/en/latest/index.html) is an open-source web application for monitoring and managing Celery clusters. It provides real-time information about the status of Celery workers and tasks."

If you have installed all the development requirements, flower is already installed.

To run flower, execute:

```
$ celery -A parlhist flower
```

Then browse to http://localhost:5555 on your local machine to visit the flower dashboard.