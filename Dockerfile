FROM python:3.7-slim-buster

RUN apt-get update && apt-get -y install libgl1-mesa-glx libglib2.0-0

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /home
COPY . /home
RUN pip3 install -r requirements.txt
RUN pip install gunicorn

EXPOSE 5000
EXPOSE 80
