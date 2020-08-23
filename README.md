# Copy-Paste-Blend Image Generation

Human-operated artificial image generation and labeling tool.

## Overview

The image generation tool provides two main functionalities so far:
1. Labeling existing objects in an image through bounding boxes.
2. Placing new objects in an image.

To this end, the tool requires two main inputs:
1. Sources images that the user wishes to label or augment
2. Object masks that the user wishes to insert to other images.

Future functionalities that the tool can provide:
- Labeling through segmentation, in order to more precisely label objects for semantic segmentation tasks, or even generate the object masks through the tool. (In the current version, the user provides the objects masks, which have to be obtained through segmentation-labeling).
- Training models directly through the web interface: both GANs for object masks and Object Detectors.

## Usage

The webapp is written in Python using Flask and served with Gunicorn. Deployment is easy as the entire application and its environment are containerized with Docker.\
Since the application is containerized, the only required dependencies are Docker itself. So make sure Docker is installed on your system (available on all platforms).\
To build the Docker image, run the following command in the root app directory:
```
docker build -t pestapp .
```
The Docker image will be available locally as `pestapp`. Run the container by executing the `run.sh` script:
```
bash run.sh
```
Note: This works for both Windows and Unix systems.

On Unix systems, you can also run the script as an executable:
```
./run.sh
```
Note: Make sure the `run.sh` script is executable by running `chmod u+x run.sh`.


The application will then be available at `localhost:5000`. The instructions to use the app are available on the web interface.
It can be tested using the files located in `static/sample`.
