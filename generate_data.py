import os
import time
import random
import cv2 as cv
import numpy as np

MASK_ROOT = 'pest_detection/datasets/aub_11_11/mask_samples/masks'
MAX_EXT = ('.png')

def show_img(image, title='image'):
    
    """ Display image with default title"""
    
    cv.imshow(title, image)
    cv.waitKey(0)
    cv.destroyAllWindows()


def load_pest_masks(all_pests, stage='adult'):
    
    """Load provided pest masks from input directory"""
    
    pest_masks = {}
    for pest_name in all_pests:
        pest_mask_paths = []
        for mask_name in os.listdir(MASK_ROOT):
            if mask_name.endswith(MASK_EXT) and 'mask' in mask_name and 'masks' not in mask_name:
                if pest_name in mask_name and stage in mask_name:
                    pest_mask_paths.append(os.path.join(root_path, mask_name))
        pest_masks[pest_name] = pest_mask_paths
    return pest_masks


def click_and_crop(event, x, y, flags, param):
    
    """Handle click events for object annotation and placement"""

    # Set global variables for generated and labeled locations
    global desired_locations, existing_boxes, placing, cropping
    
    ## On Left-Mouse-Click: Label Object
    # On Left-Mouse-Click-Down: Set starting bounding box coordinates
    if flags == cv.EVENT_FLAG_LBUTTON and event == cv.EVENT_LBUTTONDOWN:
        # Append (min_x, min_y) to labeling list
        existing_boxes.append((x,y))
        cropping = True
    # On Left-Mouse-Click-Up: Set end bounding box coordinates
    elif flags == cv.EVENT_FLAG_LBUTTON and event == cv.EVENT_LBUTTONUP:
        cropping = False
        existing_boxes[-1] = [existing_boxes[-1], (x,y)]
        cv.rectangle(clone, existing_boxes[-1][0], existing_boxes[-1][1], (0, 255, 0), 2)
        cv.imshow("image", clone)
    elif flags == (cv.EVENT_FLAG_SHIFTKEY + cv.EVENT_FLAG_LBUTTON) and event == cv.EVENT_LBUTTONDOWN:
        desired_locations.append((x,y))
        placing = True
    elif flags == (cv.EVENT_FLAG_SHIFTKEY + cv.EVENT_FLAG_LBUTTON) and event == cv.EVENT_LBUTTONUP:
        placing = False
        corners = [0, 0]
        corners[0] = (desired_locations[-1][0]-10, desired_locations[-1][1]-10)
        corners[1] = (desired_locations[-1][0]+10, desired_locations[-1][1]+10)
        cv.rectangle(clone, corners[0], corners[1], (0, 0, 255), 2)
        cv.imshow("image", clone)


def display_drawing_instructions():

    """Display tool instructions in a friendly format"""
    
    print('='*(142-7))
    print('Please follow these instructions carefully:')
    print("""Click on the image to choose an object location, then press the number corresponding to the desired object from the options below.""")
    for idx, pest in enumerate(all_pests):
        print('{:d}- {:s}'.format(idx + 1, pest.upper()))
    print('Press "r" to reset your choices.\nPress "q" when you\'re done.')
    print('='*(142-7))


def get_dir_path(prompt_dir):
    
    """Get user input directory"""
    
    dir_path = ''
    while os.path.isdir(dir_path) is False:
        if dir_path != '':
            print('  Path is invalid, or directory does not exist. Try again.')
        dir_path = input('Enter path to your {:s} images directory: '.format(prompt_dir))
    return dir_path


def get_image_paths():
    src_dir_path = get_dir_path('source background')
    dst_dir_path = get_dir_path('destination annotated')
    # load images in source directory
    img_exts = ('.jpg', '.jpeg', '.png')
    src_images = sorted([os.path.join(src_dir_path, f) for f in os.listdir(src_dir_path) if f.endswith(img_exts)])
    print('Found {:d} background images.'.format(len(src_images)))

    return src_images, dst_dir_path


def get_annotation_path(dst_dir_path):
    # Get user input path
    annotation_path = input('Enter annotation csv file path: ')
    # Set default path for no input
    if annotation_path == '':
        annotation_path = os.path.join(os.path.dirname(dst_dir_path), 'annotations.csv')
    # Set write mode to prevent overwrites
    write_mode = 'a'
    # if os.path.isfile(annotation_path):
    #     write_mode = 'a'

    return annotation_path, write_mode


def copy_paste(image, src_img, paste_bbox, copy_bbox, thresh=95, blending=False):
    success = False
    for i in range(paste_bbox[1][1] - paste_bbox[0][1]):
        for j in range(paste_bbox[1][0] - paste_bbox[0][0]):
            for k in range(3):
                src_px = src_img[copy_bbox[0][1] + i, copy_bbox[0][0] + j, k]
                if blending is True:
                    left_px = src_img[copy_bbox[0][1] + i - 1, copy_bbox[0][0] + j, :]
                    right_px = src_img[copy_bbox[0][1] + i + 1, copy_bbox[0][0] + j, :]
                    up_px = src_img[copy_bbox[0][1] + i, copy_bbox[0][0] + j + 1, :]
                    down_px = src_img[copy_bbox[0][1] + i, copy_bbox[0][0] + j - 1, :]
                    if src_px > 0 and up_px.mean() < 5:
                        src_px = (src_px - up_px[k])/2
                    if src_px > 0 and down_px.mean() < 5:
                        src_px = (src_px - down_px[k])/2
                    if src_px > 0 and left_px.mean() < 5:
                        src_px = (src_px - left_px[k])/2
                    if src_px > 0 and right_px.mean() < 5:
                        src_px = (src_px - right_px[k])/2
                if src_px > thresh:
                    try:
                        image[paste_bbox[0][1] + i, paste_bbox[0][0] + j, k] = src_px
                        success = True
                    except:
                        pass
    return image, success


def resize(src_img, mask_img, dst_img, safety=1.3):
    old_height, old_width = src_img.shape[:2]
    desired_height, desired_width = dst_img.shape[:2]
    scale = min([desired_height/old_height, desired_width/old_width])
    if scale < 1:
        scale = scale * safety
    new_size = (int(old_width * scale), int(old_height * scale))
    src_resized = cv.resize(src_img, new_size, interpolation=cv.INTER_AREA)
    mask_resized = cv.resize(mask_img, new_size, interpolation=cv.INTER_AREA)
    return src_resized, mask_resized


def init_resize(img, size, interpolation):
  h, w = img.shape[:2]
  c = None if len(img.shape) < 3 else img.shape[2]
  if h == w: return cv.resize(img, (size, size), interpolation)
  if h > w: dif = h
  else:     dif = w
  x_pos = int((dif - w)/2.)
  y_pos = int((dif - h)/2.)
  if c is None:
    mask = np.zeros((dif, dif), dtype=img.dtype)
    mask[y_pos:y_pos+h, x_pos:x_pos+w] = img[:h, :w]
  else:
    mask = np.zeros((dif, dif, c), dtype=img.dtype)
    mask[y_pos:y_pos+h, x_pos:x_pos+w, :] = img[:h, :w, :]
  return cv.resize(mask, (size, size), interpolation)


def get_contour(mask_img):
    contours, _ = cv.findContours(mask_img.copy(), cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    return contours[0]


def approx_contour(mask_img):

    # find mask contours
    contour = get_contour(mask_img)

    # approximate contour by rectangle and circle
    contours_poly = cv.approxPolyDP(contour, 3, True)
    maskRect = cv.boundingRect(contours_poly)
    maskCenter, maskRadius = cv.minEnclosingCircle(contours_poly)
    maskCenter = (int(maskCenter[0]), int(maskCenter[1]))
    maskRect = [(int(maskRect[0]), int(maskRect[1])), (int(maskRect[0] + maskRect[2]), int(maskRect[1] + maskRect[3]))]

    return maskCenter, maskRadius


def get_box_area(center, side, safety=1.0):
    side = int(side * safety)
    bbox = [(center[0] - side, center[1] - side), (center[0] + side, center[1] + side)]
    return bbox


def save_annotations(annotations, annotation_path, write_mode):
    with open(annotation_path, write_mode) as f:
        f.write(annotations)


def update_classes(annotation_path):
    classes_path = os.path.join(os.path.dirname(annotation_path), 'classes.csv')
    with open(annotation_path, 'r') as f:
        annotations = f.readlines()
    pests = []
    for line in annotations:
        pest = line.strip().split(',')[-1]
        if len(pest) > 0:
            pests.append(pest)
    pests = set(pests)
    classes = ''
    for idx, pest in enumerate(pests):
        classes = classes + '{:s},{:d}\n'.format(pest, idx)
    with open(classes_path, 'w') as f:
        f.write(classes)


# define pest types and load masks
all_pests = ['phytoseilus', 'spidermite', 'whitefly']
pest_masks = load_pest_masks(all_pests)

# ask user for image directory paths and find source images
src_images, dst_dir_path = get_image_paths()

# set up annotation file
annotation_path, write_mode = get_annotation_path(dst_dir_path)

start_idx = input('Starting index (default is 0)')
try:
    start_idx = int(start_idx)
except:
    start_idx = 0


# loop over source images and generate data
for img_num, src_img_path in enumerate(src_images):

    annotations = ''

    # display progress
    print('Generating {:d}/{:d}'.format(img_num + 1, len(src_images)), end='\r')

    # load background image
    scene_img_path = src_img_path
    image = cv.imread(scene_img_path)
    image = init_resize(image, 1920, cv.INTER_AREA)

    # define destination path
    dst_image_path = os.path.join(dst_dir_path, 'whiteflies_{:d}.{:s}'.format(img_num+start_idx, src_img_path.split('.')[-1]))

    # define annotation parameters
    placing, cropping = False, False
    pest_options, desired_locations, existing_boxes, existing_pests = [], [], [], []
    alt_keys = [33, 64, 35]

    # setup annotation process
    clone, backup = image.copy(), image.copy()
    cv.namedWindow("image")
    cv.setMouseCallback("image", click_and_crop)
    if img_num == 0:
        display_drawing_instructions()

    # begin annotation process
    while True:
        # display image and read keypresses
        cv.imshow("image", clone)
        key = cv.waitKey(1) & 0xFF
        for i in range(1, len(all_pests) + 1):
            # mark pest options
            if key == ord(str(i)):
                existing_pests.append(i-1)
                corner = (existing_boxes[-1][0][0]-7, existing_boxes[-1][0][1]+7)
                cv.putText(clone, str(i), corner, cv.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2, cv.LINE_AA)
            # mark existing pests
            if key == alt_keys[i - 1]:
                pest_options.append(i-1)
                corner = (desired_locations[-1][0]-7, desired_locations[-1][1]+7)
                cv.putText(clone, str(i), corner, cv.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2, cv.LINE_AA)
        # reset annotations
        if key == ord("r"):
            pest_options, desired_locations, existing_boxes, existing_pests = [], [], [], []
            clone = backup.copy()
        # finish annotation drawing and break loop
        elif key == ord("q"):
            if len(pest_options) != len(desired_locations):
                print('Warning: Number of requested objects and locations do not match. Please press "r" to start over.')
            if len(existing_pests) != len(existing_boxes) and len(existing_pests) > 0:
                print('Warning: Number of labeled objects and locations do not match. Please press "r" to start over.')
            elif len(existing_pests) == 0:
                existing_pests = [0 for i in range(len(existing_boxes))]
                break
            else:
                break
    cv.destroyAllWindows()

    # append annotations
    if len(pest_options) == 0 and len(existing_pests) == 0:
        annotations = annotations + '{:s},,,,,\n'.format(dst_image_path)

    for idx, pest in enumerate(pest_options):

        # read pest mask and source as grayscale
        pest_mask_path = random.choice(pest_masks[all_pests[pest]])
        mask_img = cv.imread(pest_mask_path, 0)
        src_img = cv.imread(pest_mask_path)
        # resize mask and source images
        src_img, mask_img = resize(src_img, mask_img, image)
        # approximate contour rectangular size
        maskCenter, maskRadius = approx_contour(mask_img)
        # define copy area
        copy_bbox = get_box_area(maskCenter, maskRadius, safety=1.1)
        # define paste area
        paste_bbox = get_box_area(desired_locations[idx], maskRadius, safety=1.1)
        # copy and paste
        image, write_annotations = copy_paste(image, src_img, paste_bbox, copy_bbox, thresh=100, blending=True)

        # append annotations
        if write_annotations is True:
            annotations = annotations + '{:s},{:d},{:d},{:d},{:d},{:s}\n'.format(dst_image_path,
                                                                                 *paste_bbox[0],
                                                                                 *paste_bbox[1],
                                                                                 all_pests[pest])
    for box, pest in zip(existing_boxes, existing_pests):
        annotations = annotations + '{:s},{:d},{:d},{:d},{:d},{:s}\n'.format(dst_image_path,
                                                                             *box[0],
                                                                             *box[1],
                                                                             all_pests[pest])

    # save image
    cv.imwrite(dst_image_path, image)

    # write csv annotation file
    save_annotations(annotations, annotation_path, write_mode)

# update csv classes file
update_classes(annotation_path)
print('Saved annotations and classes. Done.')
