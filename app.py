import os
import shutil
import datetime
from flask import Flask, redirect, url_for, render_template, Response
from flask import session, request
from werkzeug.utils import secure_filename

import gen

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

@app.route('/')
def test():
    return render_template('index.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
       

def get_request_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        req_ip = request.environ['REMOTE_ADDR']
    else:
        req_ip = request.environ['HTTP_X_FORWARDED_FOR']
    return req_ip


def get_dirnames(root_dir):
    src_img_dir = os.path.join(root_dir, 'images')
    masks_dir = os.path.join(root_dir, 'masks')
    output_dir = os.path.join(root_dir, 'output')
    return src_img_dir, masks_dir, output_dir


@app.route('/upload', methods=['POST'])
def upload():
    try:
        if request.method == 'POST':
            # Get request information and generate session id
            req_ip = get_request_ip()
            req_ip = req_ip.replace('.', '')
            now = datetime.datetime.utcnow()
            now = str(int(now.timestamp()*(10**6)))
            sid = hex(int(now+req_ip, 16))
            # set tmp dirnames
            root_dir = f'static/tmp_{sid}'
            src_img_dir, masks_dir, output_dir = get_dirnames(root_dir)
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

    return redirect(url_for('test'))


@app.route('/generate', methods=['POST'])
def generate():
    try:
        if request.method == 'POST':
            label_info = request.json
            required_keys = ['coordinates', 'annotation_filename', 'classes_filename', 'save_annotations', 'save_classes', 'sid']
            
            if not (set(required_keys) == set(label_info.keys())):
                return Response('{"error": "Missing form information."}', status=400, mimetype='application/json')
        
            root_dir = f'static/tmp_{label_info["sid"]}'
            src_img_dir, masks_dir, output_dir = get_dirnames(root_dir)
            
            zfile = gen.generate(
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
    
