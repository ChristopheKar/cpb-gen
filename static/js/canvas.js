// Define main variables
var colors = ['#ff0000', '#32a852', '#314ba8']
var coordinates = {};
var previousActions = [];
var canvas = document.getElementById('myCanvas');
var ctx = canvas.getContext('2d');
var rect = {};
var drag = false;
var moved = false;
var imageObj = null;
var imageFnames = [];
var currentImgIdx = 0;
var maxCanvasH;
var maxCanvasW;


// Resize elements and set variables
function resizeCanvas() {
    var rowHeight = ($('body').innerHeight() - $('#headerTitle').outerHeight() - $('#footer').outerHeight())*0.98;
    $('#mainRow').height(rowHeight);
    var canvasRowHeight = (rowHeight - $('#infoRow').outerHeight());
    $('#canvasRow').height(canvasRowHeight);
    maxCanvasH = $('#canvasRow').height();
    maxCanvasW = $('#canvasRow').width();
    loadAndDrawImage(currentImgIdx);
}


// Set global variable for image filenames
function setImageFiles(imglist) {
    imageFnames = imglist;
    for (var i = 0; i < imageFnames.length; i++) {
        coordinates[i] = {existingObjects: [], newObjects: []}
        coordinates[i].fname = imageFnames[i];
    }
}


// Get selected object index from selector
function getCurrentObject() {
    // Get selected object
    var selectedVal = $('#objectSelector').val();
    // Get possible object values
    var objOptions = $('#objectSelector option');
    var objValues = $.map(objOptions ,function(option) {
        return option.value;
    });
    if ((selectedVal !== "") && (objValues.includes(selectedVal))) {
        // Get selected object index
        var idx = objValues.findIndex(val => val === selectedVal) - 1;
        return {'index': idx, 'value': selectedVal}
    }
    return {'index': -1, 'value': ""}
}


// Load and display image on canvas
function loadAndDrawImage(curImIdx) {
    // Create an image object. This is not attached to the DOM and is not part of the page.
    imageObj = new Image();
    // When the image has loaded, draw it to the canvas
    imageObj.onload = function() {
        // Set filename in info box
        $('#respMsg').removeClass('text-success').addClass('text-info');
        $('#respMsg').text('[' + (curImIdx+1) + '/' + imageFnames.length + '] ' + imageFnames[curImIdx]);
        // Set canvas size.
        canvas.width  = Math.min(maxCanvasW, imageObj.naturalWidth);
        canvas.height = Math.min(maxCanvasH, imageObj.naturalHeight);
        coordinates[curImIdx].originalWidth = imageObj.naturalWidth;
        coordinates[curImIdx].originalHeight = imageObj.naturalHeight;
        redraw();
    }
    // Set the source of the image to load
    imageObj.src = '/static/tmp_' + $('.download').attr('id') + '/images/' + imageFnames[curImIdx];
};


// clear canvas and redraw image and annotations
function redraw() {
    $('#myCanvas').removeClass('h-100').removeClass('w-100');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(imageObj, 0, 0, canvas.width, canvas.height);
    coordinates[currentImgIdx].existingObjects.forEach(item => drawRect(item.idx, item.xmin, item.ymin, item.width, item.height));
    coordinates[currentImgIdx].newObjects.forEach(item => drawPoint(item.idx, item.x, item.y));
    if (rect.hasOwnProperty('w')) {
        drawRect(0, rect.startX, rect.startY, rect.w, rect.h)
    }
}


// draw point with color and text
function drawPoint(idx, x, y) {
    ctx.fillStyle = colors[idx];
    ctx.fillRect(x, y, 2, 2);
    ctx.font = "10px Arial";
    ctx.fillText(idx, x-2, y-5);
};


// draw point with color and text
function drawRect(idx, x, y, w, h) {
    ctx.strokeStyle = colors[idx];
    ctx.fillStyle = colors[idx];
    ctx.strokeRect(x, y, w, h);
    ctx.font = "10px Arial";
    ctx.fillText(idx, (x + w/2 - 3), (y + h/2 + 3));
};


// Draw point at location on right-click
$('body').on('contextmenu', '#myCanvas', function(e) {
    selectedObject = getCurrentObject();
    if (selectedObject.index !== -1) {
        // Find mouse-click location X Y
        var ptX = e.originalEvent.layerX - e.originalEvent.target.offsetLeft;
        var ptY = e.originalEvent.layerY - e.originalEvent.target.offsetTop;
        coordinates[currentImgIdx].newObjects.push({
            'object': selectedObject.value,
            'idx': selectedObject.index,
            'x': ptX,
            'y': ptY,
            'imageDisplayWidth': canvas.width,
            'imageDisplayHeight': canvas.height,
        });
        previousActions.push('generate');
        drawPoint(selectedObject.index, ptX, ptY);
    }
    return false;
});


// Start drawing on Left-Mouse Down
function mouseDown(e) {
    if (e.which === 1) {
      rect.startX = e.layerX - e.target.offsetLeft;
      rect.startY = e.layerY - e.target.offsetTop;
      drag = true;
    }
}


// Stop drawing on Left-Mouse Up and append object
function mouseUp(e) {
    if (e.which === 1) {
      if (moved) {
        selectedObject = getCurrentObject();
        if (selectedObject.index !== -1) {
            coordinates[currentImgIdx].existingObjects.push({
                'object': selectedObject.value,
                'idx': selectedObject.index,
                'xmin': rect.startX,
                'ymin': rect.startY,
                'xmax': rect.startX - rect.w,
                'ymax': rect.startY - rect.h,
                'width': rect.w,
                'height': rect.h,
                'imageDisplayWidth': canvas.width,
                'imageDisplayHeight': canvas.height,
            });
            previousActions.push('label');
        }
      }
      rect = {};
      drag = false;
      moved = false;
    }
    redraw();
}


// Draw on mouse move while Left-Click Down
function mouseMove(e) {
    if (e.which === 1) {
        if (drag) {
            moved = true;
            rect.w = (e.layerX - e.target.offsetLeft) - rect.startX;
            rect.h = (e.layerY - e.target.offsetTop) - rect.startY;
            redraw();
            selectedObject = getCurrentObject();
            if (selectedObject.index !== -1) {
                ctx.strokeStyle = colors[selectedObject.index];
            } else {
            ctx.strokeStyle = colors[0];
            }
            ctx.strokeRect(rect.startX, rect.startY, rect.w, rect.h);
        }
    }
}


$('#readyDiv').on('ready', function() {
    
    // Resize canvas and load image
    $('window').on('resize', resizeCanvas);
    resizeCanvas();
    currentImgIdx = 0;
    loadAndDrawImage(currentImgIdx);
    
    // Set event listeners for mouse drawing
    canvas.addEventListener('mousedown', mouseDown, false);
    canvas.addEventListener('mouseup', mouseUp, false);
    canvas.addEventListener('mousemove', mouseMove, false);
    
    // Set clear all event trigger
    $('#clearBtn').click(function() {
        coordinates[currentImgIdx].existingObjects = [];
        coordinates[currentImgIdx].newObjects = [];
        rect = {};
        redraw();
    });
    
    // Set undo event trigger
    $('#undoBtn').click(function() {
        lastAction = previousActions[previousActions.length - 1]
        previousActions.pop();
        if (lastAction === 'label') {
            coordinates[currentImgIdx].existingObjects.pop();
        } else if (lastAction === 'generate') {
            coordinates[currentImgIdx].newObjects.pop();
        }
        redraw();
    });
    
    // Set previous image event trigger
    $('#prevBtn').click(function() {
        if (currentImgIdx > 0) {
            currentImgIdx = currentImgIdx - 1;
            previousActions = [];
            loadAndDrawImage(currentImgIdx);
        }
    });
    
    // Set next image event trigger
    $('#nextBtn').click(function() {
        if (currentImgIdx < (imageFnames.length - 1)) {
            currentImgIdx = currentImgIdx + 1;
            previousActions = [];
            loadAndDrawImage(currentImgIdx);
        }
    });
});

$('#generate').on('click', function() {
    $('#respMsg').text('Generating images, please wait...');
    $.ajax({
        type:'POST',
        method: 'POST',
        url:'/generate',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({
            'coordinates': coordinates,
            'annotation_filename': $('#annName').val(),
            'classes_filename': $('#clsName').val(),
            'save_annotations': $('#save-anns').val(),
            'save_classes': $('#save-classes').val(),
            'sid': $('.download').attr('id'),
        }),
        success: function(message, status, data) {
          console.log(data.status, data.statusText, "message:", message.message);
          $('#respMsg').removeClass('text-danger').removeClass('text-info').addClass('text-success');
          $('#respMsg').text('Generation successful!');
          $('.download').attr('href', message.filepath);
          $('.download').prop('hidden', false);
        },
        error: function(data) {
          console.log(data);
          $('#respMsg').removeClass('text-success').addClass('text-danger');
          errorMsg = JSON.parse(data.responseText).error;
          console.log(data.status, data.statusText, "error:", errorMsg);
          $('#respMsg').text(errorMsg);
        }
    });
    return false;
});
