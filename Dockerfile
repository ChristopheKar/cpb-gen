FROM python:3.7-slim-buster

RUN apt-get update && apt-get -y install git build-essential libgl1-mesa-glx libglib2.0-0 libopencv-dev

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /
## Install YOLOv4 Darknet
RUN git clone https://github.com/AlexeyAB/darknet.git && cd /darknet && \
	sed -i 's/GPU=.*/GPU=0/' Makefile && \
	sed -i 's/CUDNN=.*/CUDNN=0/' Makefile && \
	sed -i 's/OPENCV=.*/OPENCV=1/' Makefile && \
	sed -i 's/OPENMP=.*/OPENMP=0/' Makefile && \
	make


  WORKDIR /home
  COPY . /home
  RUN python3 -m pip install --upgrade pip && pip3 install -r requirements.txt
  RUN pip install gunicorn
