import os
import json
import random

from imutils import *

# path to labels json file
labels_path = 'coordinates.json'
# path to image source and destination dirs
IMAGES_ROOT = 'src'
IMAGES_DST = 'dst'
# path to masks source dir and allowable extensions
MASK_ROOT = 'mask_samples/masks'
MASK_EXT = ('.png')
# object names
all_objects = ['phytoseilus', 'spidermite', 'whitefly']
# output annotation file path
annotation_path = 'a.csv'
# write mode: append to existing file
write_mode = 'a'

# load object masks
object_masks = load_object_masks(MASK_ROOT, MASK_EXT, all_objects)
# create output dirs
if not os.path.exists(IMAGES_DST):
    os.makedirs(IMAGES_DST)
    

# load and parse labels json file
with open(labels_path, 'r') as f:
    labels = json.load(f)
    
images = {}
for img in labels['images']:
    images[img['id']] = img

classes = {}
for cat in labels['categories']:
    classes[cat['id']] = cat['name']
    
annotations = {}
for item in labels['annotations']:
    annotations[item['image_id']] = annotations.get(item['image_id'], []) + [{'box': item['bbox'], 'class': item['category_id']}]

generations = {}
for item in labels['generations']:
    generations[item['image_id']] = generations.get(item['image_id'], []) + [{'point': item['point'], 'class': item['category_id']}]
    

# loop over images
for iid, iinfo in images.items():
    
    # get image path and info
    src_img_path = os.path.join(IMAGES_ROOT, iinfo['file_name'])
    img_name, img_ext = os.path.splitext(iinfo['file_name'])
    dst_image_path = os.path.join(IMAGES_DST, f'{img_name}_{iid}{img_ext}')
    
    # load image
    image = cv.imread(src_img_path)
    image = init_resize(image, 1920, cv.INTER_AREA)
    
    # initialize annotations
    annotation = ''
    
    # append labels to annotations
    ainfo = annotations[iid]
    for annot in ainfo:
        oname = classes[annot['class']]
        annotation = annotation + '{:s},{:d},{:d},{:d},{:d},{:s}\n'.format(dst_image_path,
                                                                           *annot['box'],
                                                                           oname)
    # generate objects in image   
    ginfo = generations[iid]
    for annot in ginfo:
        oname = classes[annot['class']]
        # read pest mask and source as grayscale
        pest_mask_path = random.choice(object_masks[oname])
        mask_img = cv.imread(pest_mask_path, 0)
        src_img = cv.imread(pest_mask_path)
        # resize mask and source images
        src_img, mask_img = resize(src_img, mask_img, image)
        # approximate contour rectangular size
        maskCenter, maskRadius = approx_contour(mask_img)
        # define copy area
        copy_bbox = get_box_area(maskCenter, maskRadius, safety=1.1)
        #copy_bbox = [(0, 0), (37, 37)]
        # define paste area
        paste_bbox = get_box_area(annot['point'], maskRadius, safety=1.1)
        # copy and paste
        image, write_annotations = copy_paste(image, src_img, paste_bbox, copy_bbox, thresh=105, blending=False)

        # append annotations
        if write_annotations is True:
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
    save_annotations(annotation, annotation_path, write_mode)

# update csv classes file
update_classes(annotation_path)
print('Saved annotations and classes. Done.')
    
    
