#!/bin/bash
docker run -it --rm -v $PWD:/home -p 80:80 pestapp gunicorn -w 2 --reload --bind 0.0.0.0:80 --log-level debug wsgi:app
