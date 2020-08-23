var imageFnames;
var maskFnames;

function toggleForm(toggle) {
    $("#srcImages").prop("disabled", !toggle);
    $("#maskImages").prop("disabled", !toggle);
    $("#upload").prop("disabled", !toggle);
    $("#generate").prop("disabled", toggle);
    $("#save-anns").prop("disabled", toggle);
    $("#save-classes").prop("disabled", toggle);
    $("#submit").prop("disabled", toggle);
    $("#objectSelector").prop("disabled", toggle);
    $("#objectEditor").prop("disabled", toggle);
    $("#objedit").prop("disabled", toggle);
    $("#annName").prop("disabled", toggle);
    $("#clsName").prop("disabled", toggle);
}

// Dynamically add or remove objects from select menu
$('#objedit').on('click', function() {
    var newObjectName = $('#objectEditor').val();
    var objOptions = $('#objectSelector option');
    var objValues = $.map(objOptions ,function(option) {
        return option.value;
    });
    if (newObjectName !== "") {
        if (objValues.includes(newObjectName)) {
            $('#objectSelector option[value=' + newObjectName.toLowerCase() + ']').remove();
        } else {
            $('#objectSelector').append('<option value="' + newObjectName.toLowerCase() + '">' + (objOptions.length - 1) + ': ' + newObjectName + '</option>')
        }
    }
    $('#objectEditor').val('');
});

// Disable Enter to Submit
$('#mainForm').on('keyup keypress', function(e) {
    var keyCode = e.keyCode || e.which;
    if (keyCode === 13) { 
        e.preventDefault();
        return false;
    }
});

// Disable Enter to Submit
$('#uploadForm').on('keyup keypress', function(e) {
    var keyCode = e.keyCode || e.which;
    if (keyCode === 13) { 
        e.preventDefault();
        return false;
    }
});

window.onload = toggleForm(true);

$('#infoBtn').click(function() {
    console.log('info');
    $('#infoModal').modal('show');
});

$('#srcImages').change(function(e) {
    $("#srcImagesLbl").html($("#srcImages")[0].files.length + ' images selected');
});

$('#maskImages').change(function(e) {
    console.log(e);
    $("#maskImagesLbl").html($("#maskImages")[0].files.length + ' masks selected');
});

$('#upload').on('click', function() {
    postData = new FormData();
    for (var i = 0; i < $("#srcImages")[0].files.length; i++) {
        postData.append('images[]', ($("#srcImages")[0].files[i]));
    }
    for (var i = 0; i < $("#maskImages")[0].files.length; i++) {
        postData.append('masks[]', ($("#maskImages")[0].files[i]))
    }
    $('#respMsg').text('Uploading, please wait...');
    $.ajax({
        type:'POST',
        method: 'POST',
        url:'/upload',
        processData: false,
        contentType: false,
        data : postData,
        success: function(message, status, data) {
          console.log(data.status, data.statusText, "message:", message.message);
          $('#respMsg').removeClass('text-danger').addClass('text-success');
          $('#respMsg').text('Upload successful!');
          toggleForm(false);
          $('.download').attr('id', message.sid);
          $('#infoDiv').hide();
          $('#myCanvas').prop('hidden', false);
          imageFnames = message.images;
          setImageFiles(imageFnames);
          $('#readyDiv').trigger('ready');
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
