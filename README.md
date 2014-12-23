# Snakebite

Snakebite is built with Python, and more specifically with Falcon framework and MongoEngine (python client for MongoDB).

To get started, please follow instructions below on how to setup your environment to run Snakebite

## Instructions

First, clone this repository onto your local machine

```
$ git clone https://github.com/wheresmybento/snakebite.git
$ cd snakebite
```

We first need to install all the dependencies or packages needed.
You may prefer to setup a virtual env first for better package management.

```
$ python setup.py develop
```

Once dependencies are installed, we just need to run the server!

```
$ cd snakebite
$ gunicorn example:api
```

Point your browser to `http://localhost:8000/restaurants``` to see the example json response from our code!


## TODO

1. Setup MongoDB and models
2. tests
3. use colander for management of requests
4. controllers to be used instead of a one-python-file app.
