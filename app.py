import os
from uuid import uuid4
import shutil
import datetime
from flask import Flask, redirect, url_for, render_template, Response
from flask import session, request
from werkzeug.utils import secure_filename

import generation, detection

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/gen')
def gen():
    return render_template('generate.html')


@app.route('/det')
def det():
    return render_template('detect.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_request_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        req_ip = request.environ['REMOTE_ADDR']
    else:
        req_ip = request.environ['HTTP_X_FORWARDED_FOR']
    return req_ip


def get_dirnames(root_dir, mode='gen'):
    if (mode == 'gen'):
        src_img_dir = os.path.join(root_dir, 'images')
        masks_dir = os.path.join(root_dir, 'masks')
        output_dir = os.path.join(root_dir, 'output')
        return src_img_dir, masks_dir, output_dir
    else:
        src_img_dir = os.path.join(root_dir, 'images')
        output_dir = os.path.join(root_dir, 'detections')
        lbl_dir = os.path.join(output_dir, 'labels')
        img_dir = os.path.join(output_dir, 'images')
        return src_img_dir, lbl_dir, img_dir


@app.route('/upload', methods=['POST'])
def upload():
    try:
        if request.method == 'POST':
            # Get request information and generate session id
            sid = str(uuid4()).replace('-', '')
            # set tmp dirnames
            root_dir = f'static/tmp_{sid}'
            src_img_dir, masks_dir, output_dir = get_dirnames(root_dir, 'gen')
            # create tmp dirs
            if os.path.exists(root_dir):
                shutil.rmtree(root_dir)
            os.makedirs(root_dir)
            os.makedirs(masks_dir)
            os.makedirs(src_img_dir)
            os.makedirs(output_dir)
            # check if the post request has the file part
            if ('images[]' in request.files) and ('masks[]' in request.files):
                images = request.files.getlist('images[]')
                masks = request.files.getlist('masks[]')
                saved_images = []
                for img in images:
                    if allowed_file(img.filename):
                        filename = secure_filename(img.filename)
                        img.save(os.path.join(src_img_dir, filename))
                        saved_images.append(filename)
                saved_masks = []
                for img in masks:
                    if allowed_file(img.filename):
                        filename = secure_filename(img.filename)
                        img.save(os.path.join(masks_dir, filename))
                        saved_masks.append(filename)

                if (len(saved_images) == 0) or (len(saved_masks) == 0):
                    return Response('{"error": "Invalid image files."}', status=400, mimetype='application/json')
                else:
                    return {"message": "Successful upload!", "images": saved_images, "masks": saved_masks, "sid": sid}, 200
            else:
                return Response('{"error": "Missing images or masks."}', status=400, mimetype='application/json')
    except Exception as e:
        print(repr(e))
        return Response('{"error": "Internal server error. Try again or contact support."}', status=500, mimetype='application/json')

    return redirect(url_for('gen'))


@app.route('/generate', methods=['POST'])
def generate():
    try:
        if request.method == 'POST':
            label_info = request.json
            required_keys = ['coordinates', 'annotation_filename', 'classes_filename', 'save_annotations', 'save_classes', 'sid']

            if not (set(required_keys) == set(label_info.keys())):
                return Response('{"error": "Missing form information."}', status=400, mimetype='application/json')

            root_dir = f'static/tmp_{label_info["sid"]}'
            src_img_dir, masks_dir, output_dir = get_dirnames(root_dir, 'gen')

            zfile = generation.generate(
                label_info['coordinates'],
                root_dir, src_img_dir, masks_dir, output_dir,
                label_info['annotation_filename'], label_info['classes_filename'],
                label_info['save_annotations'], label_info['save_classes']
            )

            return {"message": "Successful generation!", "filepath": zfile}, 200

        return Response('{"error": "Method not allowed for the requested URL."}', status=405, mimetype='application/json')

    except Exception as e:
        print(repr(e))
        return Response('{"error": "Internal server error. Try again or contact support."}', status=500, mimetype='application/json')


@app.route('/upload-det', methods=['POST'])
def upload_det():
    try:
        if request.method == 'POST':
            # Get request information and generate session id
            sid = 'det_' + str(uuid4()).replace('-', '')
            # set tmp dirnames
            root_dir = f'static/tmp_{sid}'
            src_img_dir, lbl_dir, img_dir = get_dirnames(root_dir, 'det')
            # create tmp dirs
            if os.path.exists(root_dir):
                shutil.rmtree(root_dir)
            os.makedirs(root_dir)
            os.makedirs(src_img_dir)
            os.makedirs(lbl_dir)
            os.makedirs(img_dir)
            # check if the post request has the file part
            if ('images[]' in request.files):
                images = request.files.getlist('images[]')
                saved_images = []
                for img in images:
                    if allowed_file(img.filename):
                        filename = secure_filename(img.filename)
                        img.save(os.path.join(src_img_dir, filename))
                        saved_images.append(filename)

                if (len(saved_images) == 0):
                    return Response('{"error": "Invalid image files."}', status=400, mimetype='application/json')
                else:
                    return {"message": "Successful upload!", "images": saved_images, "sid": sid}, 200
            else:
                return Response('{"error": "Missing images."}', status=400, mimetype='application/json')

        return Response('{"error": "Method not allowed for the requested URL."}', status=405, mimetype='application/json')

    except Exception as e:
        print(repr(e))
        return Response('{"error": "Internal server error. Try again or contact support."}', status=500, mimetype='application/json')

    return redirect(url_for('det'))


@app.route('/detect', methods=['POST'])
def det_det():
    try:
        if request.method == 'POST':
            # Get request information: sid
            sid = request.json['sid']
            # get tmp dirnames
            root_dir = f'static/tmp_{sid}'
            src_img_dir, lbl_dir, img_dir = get_dirnames(root_dir, 'det')

            saved_images = []
            for imgf in os.listdir(src_img_dir):
                if imgf.endswith(tuple(ALLOWED_EXTENSIONS)):
                    saved_images.append(os.path.join(src_img_dir, imgf))

            if (len(saved_images) == 0):
                return Response('{"error": "No image files."}', status=400, mimetype='application/json')

            detection.run(saved_images, os.path.dirname(img_dir))
            detected_images = []
            for file in os.listdir(img_dir):
                detected_images.append(os.path.join(img_dir, file))

            # zip output into one directory
            zname = 'detected'
            zdir = os.path.join(root_dir, zname)
            zdir_path = shutil.make_archive(zdir, 'zip', root_dir=root_dir)
            zdir_path = zdir_path.replace('/home', '')

            return {"message": "Successful detection!", "images": detected_images, "filepath": zdir_path}, 200

        return Response('{"error": "Method not allowed for the requested URL."}', status=405, mimetype='application/json')

    except Exception as e:
        print(repr(e))
        return Response('{"error": "Internal server error. Try again or contact support."}', status=500, mimetype='application/json')

    return redirect(url_for('det'))
