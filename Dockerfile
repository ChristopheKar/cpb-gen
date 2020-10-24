FROM python:3.7-slim-buster

RUN apt-get update && apt-get -y install git build-essential libgl1-mesa-glx libglib2.0-0 libopencv-dev

WORKDIR /
## Install YOLOv4 Darknet
RUN git clone https://github.com/pjreddie/darknet.git && cd /darknet && \
	sed -i 's/GPU=.*/GPU=0/' Makefile && \
	sed -i 's/CUDNN=.*/CUDNN=0/' Makefile && \
	sed -i 's/OPENCV=.*/OPENCV=1/' Makefile && \
	sed -i 's/OPENMP=.*/OPENMP=0/' Makefile && \
	sed -i 's/print r/print(r)/' python/darknet.py && \
	sed -i 's;CDLL("libdarknet.so", RTLD_GLOBAL);CDLL("/darknet/libdarknet.so", RTLD_GLOBAL);' python/darknet.py && \
	make


WORKDIR /home
COPY . /home
RUN python3 -m pip install --upgrade pip && pip3 install -r requirements.txt
RUN pip install gunicorn
