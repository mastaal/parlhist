# Developing parlhist

Some notes and tips for developing parlhist

## Running rabbitmq

Rabbitmq is the recommended task queue for celery. You can run a local instance using:

```
$ podman run -it --rm --name rabbitmq -p 5672:5672 rabbitmq
```

(If you use docker, just change 'podman' into 'docker')