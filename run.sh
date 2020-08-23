#!/bin/bash
docker run -it --rm -v $PWD:/home -p 5000:5000 pestapp gunicorn -w 2 --reload --bind 0.0.0.0:5000 --log-level debug wsgi:app
