#!/bin/bash
docker run -it --rm -v $PWD:/home -p 80:80 pestdet gunicorn -w 2 --reload --timeout 500 --bind 0.0.0.0:80 --log-level debug wsgi:app
