import os
import sys
import cv2 as cv
import numpy as np

DARKNET_PATH = '/darknet/python'
os.environ['DARKNET_PATH'] = DARKNET_PATH
sys.path.insert(0, DARKNET_PATH)
import darknet as dn

IMG_EXTS = tuple(['.jpg','.png','.jpeg'])
color_list = [(0,255,0),(0,0,255),(255,0,0),(0,255,255),(0,0,0),(255,255,0),(255,0,255),(255,0,125),(0,255,125),(0,125,255)]


def clamp(n, lower, upper):
    return max(min(upper, n), lower)


def load(cfg_path, data_path, weights_path):
    """Load Darknet network and meta information"""
    net = dn.load_net(cfg_path.encode(), weights_path.encode(), 0)
    meta = dn.load_meta(data_path.encode())
    return net, meta


def detect(filepath, net, meta, thresh=0.45, hier_thresh=0.50):

    predictions = dn.detect(net, meta, filepath.encode(), thresh, hier_thresh)

    coordinates_new = np.array([])
    if not predictions:
        return coordinates_new

    names = []
    for name in meta.names:
        if name == None:
            break
        else:
            names.append(name)

    img = cv.imread(filepath)
    img = cv.putText(img,
                     'Count: {} whiteflies'.format(len(predictions)),
                     (2, 15),
                     cv.FONT_HERSHEY_SIMPLEX,
                     0.5,
                     (255,255,255),
                     2,
                     cv.LINE_AA)

    height, width = img.shape[:2]
    for i in range(len(predictions)):
        classes = names.index(predictions[i][0])
        top = int(clamp((predictions[i][2][1] - (predictions[i][2][3]/2)),0, height))
        left = int(clamp((predictions[i][2][0] - (predictions[i][2][2]/2)),0, height))
        right = int(clamp((predictions[i][2][0] + (predictions[i][2][2]/2)),0, height))
        bottom = int(clamp((predictions[i][2][1] + (predictions[i][2][3]/2)),0, height))
        top_txt = top-10 if top-10 > 0 else 0
        confidence = predictions[i][1]
        img = cv.putText(img,
                         predictions[i][0].decode('utf-8'),
                         (left,top_txt),
                         cv.FONT_HERSHEY_SIMPLEX,
                         0.5,
                         (255,255,255),
                         2,
                         cv.LINE_AA)
        img = cv.rectangle(img, (left, top), (right,bottom), color_list[classes], 3)
        coordinates = [classes, left, top, right, bottom, confidence]
        coordinates_new = np.append(coordinates_new,coordinates)

    return coordinates_new, img


def run(files, export_dir, thresh=0.45, hier_thresh=0.5):

    net_dir = os.path.abspath('network')
    cfg = os.path.join(net_dir, 'whiteflies.cfg')
    data = os.path.join(net_dir, 'whiteflies.data')
    weights = os.path.join(net_dir, 'whiteflies.weights')

    net, meta = load(cfg, data, weights)

    if not os.path.isdir(export_dir):
        raise NameError(f'Export directory {export_dir} does not exist.')

    if isinstance(files, list):
        images = [file for file in files if (file.endswith(IMG_EXTS) and os.path.exists(file))]
    elif isinstance(files, str):
        if os.path.isdir(files):
            images = [os.path.join(files, file) for file in os.listdir(files) if (file.endswith(IMG_EXTS) and os.path.exists(file))]
        elif (files.endswith(IMG_EXTS)):
            images = [filename]
        elif filename.endswith('.txt'):
            with open(filename,'r') as f:
                r = f.read()
            images = r.strip().split('\n')
    else:
        raise TypeError('files must be of type <str> or <list>')

    for filepath in images:
        c, img = detect(filepath, net, meta, 0.45, 0.50)
        c = np.reshape(c, [int(np.shape(c)[0]/6),6])
        a = np.array2string(c,formatter={'float': '{: 0.3f}'.format})
        a = a.replace('[','').replace(']','')
        a = a.strip()
        a = a.replace('  ',' ').replace('\n ','\n').replace('0.000','0').replace('1.000','1')

        new_img_name = os.path.join(export_dir, 'images', filepath.split('/')[-1])
        new_lbl_name = os.path.join(export_dir, 'labels', filepath.split('/')[-1][0:-3] + 'txt')
        cv.imwrite(new_img_name, img)
        with open(new_lbl_name, 'w') as f:
            f.write(a)
