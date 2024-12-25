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
var ThumbnailUploadModal = undefined;
var ThumbnailOrgFile = undefined;
var ImageEditorModal = undefined;
var ImageEditor = undefined;
var ImageEditorOrgFile = undefined;
var ImageUploadList = [];
tui.usageStatistics = false

jQuery(document).ready(function () {
  //Init the editor
  ImageEditorModal = new bootstrap.Modal(document.getElementById('image-editor-modal'));
  ThumbnailUploadModal = new bootstrap.Modal(document.getElementById('thumbnail-upload-modal'));
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

  // Add an event listener to the input
  $('#thumbnail').bind('change', (event) => { 
    const fileInput = event.target;
    const files = fileInput.files;

    if (files.length > 0) {
      const file = files[0];
      const blob = new Blob([file], { type: file.type });
      if (file.type.match(/image.*/)) {
        ThumbnailOrgFile.thumb = blob;

        //Get the image dimentions
        UC.getImageDimensions(blob).then((size) => {
          ThumbnailOrgFile.thumb_metadata = {
            width: size.width,
            height: size.height,
            mimetype: file.type,
          }

          //bma_uuid excists after the file is uploaded
          if ("bma_uuid" in ThumbnailOrgFile) {
            UC.uploadThumbnailSource(ThumbnailOrgFile.bma_uuid, blob, "thumbnail", ThumbnailOrgFile.thumb_metadata).then(()=> {
              ThumbnailUploadModal.hide();
            });
          }
        });
        const fr = new FileReader();
        fr.addEventListener(
          "load",
          () => {
            dropzone.emit("thumbnail", ThumbnailOrgFile, fr.result);
          },
          false,
        );
        UC.crop(blob, 120, 120).then((file) => {
          fr.readAsDataURL(file);
          if (!("bma_uuid" in ThumbnailOrgFile))
            ThumbnailUploadModal.hide();
        })
      } else alert("Not a image");
    } else {
      console.log('No file selected');
    }
  });

  //Cancel button thumbnail Modal
  $('#thumbnail-cancel').bind('click', () => {
    ThumbnailUploadModal.hide();
    ThumbnailOrgFile = undefined;
  });

  //Delete button thumbnail Modal
  $('#thumbnail-delete').bind('click', () => {
    if (!("bma_uuid" in ThumbnailUploadModal)) {
      delete(ThumbnailUploadModal.thumb);
      delete(ThumbnailUploadModal.thumb_metadata);
      for (let thumbnailElement of ThumbnailOrgFile.previewElement.querySelectorAll(
        "[data-dz-thumbnail]"
      )) {
        thumbnailElement.alt = "";
        thumbnailElement.src = "";
      }
    } else {
      alert("Sorry cant remove if already uploaded");
    }
    ThumbnailUploadModal.hide();
    ThumbnailOrgFile = undefined;
  });

  //Init Dropzone
  dropzone = new Dropzone("#my-dropzone", {
    url: baseURL + "/api/v1/json/files/upload/",
    paramName: "file_data",
    autoProcessQueue: false,
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
    formData.append('file_metadata', JSON.stringify(metadata));
    formData.append('client', JSON.stringify({client_version: UC.client_version, client_uuid: UC.client_uuid}));

    if (file.thumb) {
      formData.append('thumbnail_data', file.thumb);
      formData.append('thumbnail_metadata', JSON.stringify(file.thumb_metadata));
    }

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
      alert("Invalid filetype: " + file.type);
    }
    if (!file.type.match(/image.*/)) {
      file.previewElement.addEventListener("click", function() {
        $("#thumbnail").val('');
        ThumbnailOrgFile = file;
        if ("thumb" in file && !("bma_uuid" in file)) {
          $("#thumbnail-delete").show();
        } else
          $("#thumbnail-delete").hide();
        ThumbnailUploadModal.show();
      });
    }
  })

  //Event triggered when the thumbnail is made 
  dropzone.on("thumbnail", file => {
    file.previewElement.addEventListener("click", function() {
      if ("thumb" in file) return;
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

    //Append images to make album when done
    ImageUploadList.push(uuid)

    file.bma_uuid = uuid;

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
    dropzone.processQueue();
  })

  //Event triggered after its done uploading
  dropzone.on("queuecomplete", _file => {
    const now = new Date;
    if (ImageUploadList.length > 0) {
      console.log("Adding album for", ImageUploadList)
      UC.createAlbum(`Uploaded ${now.toISOString()}`,"", ImageUploadList);
      ImageUploadList = [];
    }
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
