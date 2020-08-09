import os
import cv2 as cv
import numpy as np

def load_object_masks(mask_root, mask_ext, all_objects, stage='adult'):
    """Load provided object masks from input directory"""
    object_masks = {}
    for object_name in all_objects:
        object_mask_paths = []
        for mask_name in os.listdir(mask_root):
            if mask_name.endswith(mask_ext):
                if object_name in mask_name:
                    object_mask_paths.append(os.path.join(mask_root, mask_name))
        object_masks[object_name] = object_mask_paths
    return object_masks


def copy_paste(image, src_img, paste_bbox, copy_bbox, thresh=95, blending=False):
    success = False
    for i in range(copy_bbox[1][1] - copy_bbox[0][1]):
        for j in range(copy_bbox[1][0] - copy_bbox[0][0]):
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
                        image[paste_bbox[0][1] + i, paste_bbox[0][0] + j, k] = src_px + 30
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
    if h == w:
        return cv.resize(img, (size, size), interpolation)
    if h > w:
        dif = h
    else:
        dif = w
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
