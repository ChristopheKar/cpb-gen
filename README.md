# Copy-Paste-Blend Image Generation

Semi-automated artificial image generation through a copy-paste-blend pipeline.

## Overview

The image generation tool provides two main functionalities so far:
1. Labeling existing objects in an image through bounding boxes.
2. Placing new objects in an image.

To this end, the tool requires two main inputs:
1. A directory containing source images which we wish to label or augment
2. A directory containing object masks and their source images, which will be placed in new images to augment them.

As of now, the tool is not fully modular, and some things are hard-coded, like the location of the object masks and their source images, and the instruction set which is related to the specific project use-case: pest detection. So for example, the tool runs in command-line and asks the user to augment the images using 3 types of insects.

Future functionalities that the tool can provide:
- Labeling through segmentation, in order to more precisely label objects for semantic segmentation tasks, or even generate the object masks through the tool. (In the current version, the user provides the objects masks, which have to be obtained through segmentation-labeling).

The tool will be updated to be as modular as possible and as ready for web-application as it can be.

## Webapp

Developing a web-application to host this tool, is straight-forward but comes with a set of challenges and things to look out for.
The general structure would be as follows:
1. Front-end:
   - Set-up the project and environment:
      1. Listing object types
      2. Uploading object masks and source images
      3. Uploading source images
   - Drawing and labeling: (core functionality)
      1. Images will be displayed one by one in a carousel
      2. User can click on the images at desired locations to place a new object (so location selection and object type selection)
      3. User can draw a box on the imaegs at desired locations to label an existing object (so box drawing and object type selection)
      4. Processing the images (backend) and making them available for download.
2. Backend:
   - The backend will mostly rely on the existing scripts to generate the images, relying heavily on OpenCV and NumPy. The scripts will be improved and made modular so as to accept a list of locations and object types in order to label/augment images, and provide the necessary annotations files.

Main challenges and things to look out for, in my opinion:
1. It might be challenging to deal with the <canvas> layer to try to make the labeling/augmentation process as smooth as possible, and as user-friendly as possible. The user-friendliness is probably the hardest part, and the tool should include features like editing existing labels, undo, reset, saving, and similar features.

2. It is important to be careful at how the images scale on display: the images should be fit to the user's screen size, but this has to be reported to the backend as we would then need to rescale the collected coordinates for locations and bounding boxes to the original image size.

3. If the segmentation-labeling functionality is added, it would also increase the difficulty in user-friendliness, and leads to the next problem,

4. The trap of too many features, where do we stop? Is this a labeling tool or a generation tool? How friendly do we want to make it? Is it going to be the lab's go-to tool for labeling? Is it available to anyone? This also leads into the next problem,

5. DevOps: where is this hosted, is it centrally-hosted and owned by us or do we offer self-hosting? where do we keep the images when the size of the datasets inevitably grows out of hand? and most importantly, how much time is this going to take?

Finally, as mentioned a few times, I will be spending time documenting the code, and improving its modularity and functionality to make it as easy to build more on top of it.
