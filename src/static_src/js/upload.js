/* File used in /file/upload as the main JS file */

Dropzone.autoDiscover = false;
const baseURL = "";
const client_id = JSON.parse(document.getElementById('client_id').textContent);
const UC = new UploadClient(client_id, () => {
  $('#btnupload').html("Upload");
  console.log("Loaded UC client");
});

//Init base variables
var dropzone = undefined;
var ImageEditorModal = undefined;
var ImageEditor = undefined;
var ImageEditorOrgFile = undefined;
tui.usageStatistics = false

jQuery(document).ready(function () {
  //Init the editor
  ImageEditorModal = new bootstrap.Modal(document.getElementById('image-editor-modal'));
  ImageEditor = new tui.ImageEditor(document.querySelector('#my-image-editor'), {
    includeUI: {
      theme: {
        "common.bi.image": '',
      },
    },
    usageStatistics: false,
  });

  $('.tui-image-editor-header-buttons').hide();
  $('.tui-image-editor-header-logo').hide();

  //Bind upload action
  $('#btnupload').bind('click', () => dropzone.processQueue());

  //Save image from editor
  $('#editor-save-image').bind('click', () => {
    const data = ImageEditor.toDataURL();
    var blob = dataURItoBlob(data);
    const file = new File([blob], `edited-` + ImageEditorOrgFile.name, {
      type: "image/jpeg",
      lastModified: new Date(),
    });
    file.upload = {
      chunked: false,
    };
    dropzone.addFile(file);
    dropzone.emit("addedfiles", dropzone.files);
    ImageEditorOrgFile = undefined;
    ImageEditorModal.hide();
  });

  //Save image as new
  $('#editor-save-new-image').bind('click', () => {
    const data = ImageEditor.toDataURL();
    var blob = dataURItoBlob(data);
    const file = new File([blob], `edited-` + ImageEditorOrgFile.name, {
      type: "image/jpeg",
      lastModified: new Date(),
    });
    file.upload = {
      chunked: false,
    };
    dropzone.addFile(ImageEditorOrgFile);
    dropzone.addFile(file);
    dropzone.emit("addedfiles", dropzone.files);
    ImageEditorOrgFile = undefined;
    ImageEditorModal.hide();
  });

  //Cancel editor and return file back to dropzone
  $('#editor-cancel').bind('click', () => {
    dropzone.addFile(ImageEditorOrgFile);
    dropzone.emit("addedfiles", dropzone.files);
    ImageEditorOrgFile = undefined;
    ImageEditorModal.hide();
  });

  //Init Dropzone
  dropzone = new Dropzone("#my-dropzone", {
    url: baseURL + "/api/v1/json/files/upload/",
    paramName: "f",
    autoProcessQueue: false,
    complete: file => { //Function overwritten to allow for later processing
      file.previewElement.classList.remove("dz-processing");
      file.previewElement.classList.remove("dz-complete");
      file.previewElement.classList.remove("dz-success");
      file.previewElement.classList.add("dz-processing");
    },
  });

  //Event triggered just before starting upload
  //Add the extra fields here
  dropzone.on("sending", (file, xhr, formData) => {
    let metadata = {};
    let license = document.getElementById("id_license");
    metadata.license = license.options[license.selectedIndex].value;
    metadata.attribution = document.getElementById("id_attribution").value;
    if (file.type.startsWith("image/")) {
      metadata.width = file.width;
      metadata.height = file.height;
    }
    metadata.mimetype = file.type;

    // TODO: parse tags following the same rules as the default parser in
    // https://django-taggit.readthedocs.io/en/latest/custom_tagging.html#using-a-custom-tag-string-parser
    tags = document.getElementById("id_tags").value.trim();
    if (tags.length > 0) {
      metadata.tags = document.getElementById("id_tags").value.split(" ");
    };

    //Add metadata to request
    formData.append('metadata', JSON.stringify(metadata));

    //Add authenticaton to xhr
    xhr.setRequestHeader("Authorization", `Bearer ${UC.oauth.token}`);
  });

  //Event triggered when file is added
  dropzone.on("addedfile", file => {
    if (UC.allowedMimetypes.indexOf(file.type) !== -1) {
      if (UC.oauth.token) {
        formdatas.push(file.name)
        enableUploadButton();
      } else {
        $('#btnupload').html("Token ERROR");
      }
    } else {
      dropzone.removeFile(file);
      alert("Invalid filetype");
    }
  })

  //Event triggered when the thumbnail is made 
  dropzone.on("thumbnail", file => {
    file.previewElement.addEventListener("click", function() {
      console.log("Starting editor");
      ImageEditor.loadImageFromURL(file.dataURL,file.name).then( () => {
        ImageEditor.resetZoom();
        ImageEditorModal.show();
        ImageEditor.ui.resizeEditor();
        ImageEditor.ui.activeMenuEvent();
        ImageEditor.ui.clearHistory()
        ImageEditorOrgFile = file;
        dropzone.removeFile(file);
      })
    })
  });

  //Event triggered after file is uploaded
  dropzone.on("success", file => {
    const resp = JSON.parse(file.xhr.response);
    const uuid = resp.bma_response.uuid;

    //Queue file for jobs fetching and processing
    UC.addToQueue(uuid, file);

    //Make BMA scripts happy
    const index = formdatas.indexOf(file.name);
    if (index !== -1) {
      formdatas.splice(index, 1);
    }
    //Trigger BMA script enableUploadButton
    enableUploadButton();
  });

  //Event triggered after its done uploading a batch
  dropzone.on("complete", _file => {
    UC.processNext();
    dropzone.processQueue();
  })

  //Event triggered after its done uploading
  dropzone.on("queuecomplete", _file => {
    const now = new Date;
    UC.createAlbum(`Uploaded ${now.toISOString()}`,"") 
  })
});

/**
 * DataURI to Blob 
 *
 * @param {string} dataURI - Data URI 
 * @return {blob} Image 
 */
function dataURItoBlob(dataURI) {
	var byteString = atob(dataURI.split(",")[1]);
	var mimeString = dataURI.split(",")[0].split(":")[1].split(";")[0];

	var ab = new ArrayBuffer(byteString.length);
	var ia = new Uint8Array(ab);
	for (var i = 0; i < byteString.length; i++) {
	  ia[i] = byteString.charCodeAt(i);
	}
	return new Blob([ab], { type: mimeString });
}
