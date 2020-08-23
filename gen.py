import os
from shutil import make_archive
import json
import random

from imutils import *

def generate(coordinates, root_dir, src_img_dir, mask_dir, output_dir, ann_filename='annotations.csv', cls_filename='classes.csv', save_anns=True, save_classes=True):

    # set full csv file path names
    if not ann_filename.endswith('.csv'):
        ann_filename = ''.join([ann_filename, '.csv'])
    if not cls_filename.endswith('.csv'):
        cls_filename = ''.join([cls_filename, '.csv'])
    annotation_path = os.path.join(root_dir, ann_filename)
    classes_path = os.path.join(root_dir, cls_filename)
    # write mode: append to existing file
    write_mode = 'w'
    
    # get all labeled and generated objects
    raw_objects = []
    for info in coordinates.values():
        for lbl in info['existingObjects']:
            raw_objects.append((lbl['idx'], lbl['object']))
        for lbl in info['newObjects']:
            raw_objects.append((lbl['idx'], lbl['object']))
    
    raw_objects = sorted(raw_objects, key=lambda x: x[0])
    all_objects = []
    for obj in raw_objects:
        if obj[1] not in all_objects:
            all_objects.append(obj[1])
    
    # load object masks
    object_masks = load_object_masks(mask_dir, all_objects)
    
    # create output dirs
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # loop over images
    for iid, iinfo in coordinates.items():
        # get image path and info
        src_img_path = os.path.join(src_img_dir, iinfo['fname'])
        img_name, img_ext = os.path.splitext(iinfo['fname'])
        dst_image_path = os.path.join(output_dir, f'{img_name}_{iid}{img_ext}')
        
        # load image
        image = cv.imread(src_img_path)
        image = init_resize(image, 1920, cv.INTER_AREA)
        
        # initialize annotations
        annotation = ''
        
        # append labels to annotations
        ainfo = iinfo['existingObjects']
        for lbl in ainfo:
            xmin, ymin, xmax, ymax = lbl['xmin'], lbl['ymin'], lbl['xmax'], lbl['ymax']
            xrat = iinfo['originalWidth']/lbl['imageDisplayWidth']
            yrat = iinfo['originalHeight']/lbl['imageDisplayHeight']
            xmin = int(xmin*xrat)
            ymin = int(ymin*yrat)
            xmax = int(xmax*xrat)
            ymax = int(ymax*yrat)
            annotation = annotation + '{:s},{:d},{:d},{:d},{:d},{:s}\n'.format(dst_image_path,
                                                                               xmin, ymin,
                                                                               xmax, ymax,
                                                                               lbl['object'])
        # generate objects in image   
        ginfo = iinfo['newObjects']
        for lbl in ginfo:
            oname = lbl['object']
            # read pest mask and source as grayscale
            object_mask_path = random.choice(object_masks[oname])
            mask_img = cv.imread(object_mask_path, 0)
            src_img = cv.imread(object_mask_path)
            # resize mask and source images
            src_img, mask_img = resize(src_img, mask_img, image)
            # approximate contour rectangular size
            maskCenter, maskRadius = approx_contour(mask_img)
            # define copy area
            copy_bbox = get_box_area(maskCenter, maskRadius, safety=1.1)
            #copy_bbox = [(0, 0), (37, 37)]
            # define paste area
            xrat = iinfo['originalWidth']/lbl['imageDisplayWidth']
            yrat = iinfo['originalHeight']/lbl['imageDisplayHeight']
            xdiff = iinfo['originalWidth'] - lbl['imageDisplayWidth']
            ydiff = iinfo['originalHeight'] - lbl['imageDisplayHeight']
            xx = int(lbl['x']*xrat)
            yy = int(lbl['y']*yrat)
            paste_bbox = get_box_area((xx, yy), maskRadius, safety=1.1)
            # copy and paste
            image, write_annotation = copy_paste(image, src_img, paste_bbox, copy_bbox, thresh=105, blending=False)
    
            # append annotations
            if write_annotation is True:
                annotation = annotation + '{:s},{:d},{:d},{:d},{:d},{:s}\n'.format(dst_image_path,
                                                                                   *paste_bbox[0],
                                                                                   *paste_bbox[1],
                                                                                   oname)
        
        # if image contains no labels at all, append empty annotation
        if (len(ainfo) == 0) and (len(ginfo) == 0):
            annotation = annotation + f'{dst_image_path},,,,,\n'
            
        # save image
        cv.imwrite(dst_image_path, image)
    
        # write csv annotation file
        if save_anns:
            save_annotations(annotation, annotation_path, write_mode)

    # save classes file
    if save_classes:
        save_classes_file(all_objects, classes_path)
    # save coordinates json file
    with open(os.path.join(root_dir, 'coordinates.json'), 'w') as f:
        json.dump(coordinates, f)
    # zip output into one directory
    zname = 'generated'    
    zdir = os.path.join(root_dir, zname)
    zdir_path = make_archive(zdir, 'zip', root_dir=root_dir)
    
    return os.path.relpath(zdir_path)
