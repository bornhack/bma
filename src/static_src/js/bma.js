jQuery(document).ready(function () {
    ImgUpload();
    $('#id_files').trigger("change");
});

// use global var for formdatas
var formdatas = [];

function ImgUpload() {
    $('#id_files').bind('change', function (e) {
        $(this).closest('.container').find('.upload__img-wrap').remove();
        $(this).closest('.container').find('.upload__box').append('<div class="row gy-4 upload__img-wrap"></div>');
        imgWrap = $(this).closest('.container').find('.upload__img-wrap');

        var files = e.target.files;
        var filesArr = Array.prototype.slice.call(files);
        var iterator =  0;

        // get preview templates
        const pt = document.getElementById("preview-template");

        // create file metadata object from the form fields
        let metaData = {};
        let license = document.getElementById("id_license");
        metaData.license = license.options[license.selectedIndex].value;
        metaData.attribution = document.getElementById("id_attribution").value;

        // loop over selected files to show thumbnail and generate formData for each
        filesArr.forEach(function (f, index) {
            // only images for now
            if (!f.type.match('image.*')) {
                return;
            }
            var reader = new FileReader();
            reader.onload = function (e) {
                iterator++;
                var originalImage = new Image();
                originalImage.src = e.target.result;
                let clone = pt.content.cloneNode(true);
                clone.querySelector(".card").id = 'img-card-' + iterator;
                clone.querySelector(".card-title").innerHTML = f.name;
                clone.querySelector(".card-text").id = 'img-card-body-' + iterator;
                clone.querySelector(".card-footer").id = 'img-card-footer-' + iterator;
                imgWrap.append(clone);
                // create formData object for upload of this file
                let formData = new FormData();
                formData.append("f", f);
                // add metadata to form
                formData.append("metadata", JSON.stringify(metaData));
                // add csrf token
                formData.append("csrfmiddlewaretoken", document.getElementsByName("csrfmiddlewaretoken")[0].value);
                formdatas.push(formData);
                originalImage.addEventListener("load", function () {
                    // when the image is done loading fill the card
                    var thumbnailImage = createThumbnail(originalImage);
                    thumbnailImage.className = "card-img-top";
                    $("#img-card-" + iterator).prepend(thumbnailImage);
                    $("#img-card-body-" + iterator).text("Image is " + originalImage.width + " x " + originalImage.height + " pixels (aspect ratio " + ratio(originalImage.width, originalImage.height).join(":") + ")");
                    $("#img-card-footer-" + iterator).text("File size " + f.size.toLocaleString() + " bytes");
                });
            }
            reader.readAsDataURL(f);
        });
    });
}

function uploadFiles() {
    formdatas.forEach(fd => uploadFile(fd));
}

async function uploadFile(fd) {
    await fetch('/api/v1/json/files/upload/', {
        method: "POST",
        body: fd
    });
    alert('The file has been uploaded successfully.');
}

var thumbnailMaxWidth = 400;
var thumbnailMaxHeight = 400;

var createThumbnail = function (image) {
    var canvas, ctx, thumbnail, thumbnailScale, thumbnailWidth, thumbnailHeight;
    // create an off-screen canvas
    canvas = document.createElement('canvas');
    ctx = canvas.getContext('2d');

    //Calculate the size of the thumbnail, to best fit within max/width (cropspadding)
    thumbnailScale = (image.width / image.height) > (thumbnailMaxWidth / thumbnailMaxHeight) ?
    thumbnailMaxWidth / image.width :
    thumbnailMaxHeight / image.height;
    thumbnailWidth = image.width * thumbnailScale;
    thumbnailHeight = image.height * thumbnailScale;

    // set its dimension to target size
    canvas.width = thumbnailWidth;
    canvas.height = thumbnailHeight;

    // draw source image into the off-screen canvas:
    ctx.drawImage(image, 0, 0, thumbnailWidth, thumbnailHeight);

    //Draw border (optional)
    ctx.rect(0, 0, thumbnailWidth, thumbnailHeight - 1);
    ctx.strokeStyle = "#555555";
    ctx.stroke();

    // encode image to data-uri with base64 version of compressed image
    thumbnail = new Image();
    thumbnail.src = canvas.toDataURL('image/jpeg', 70);
    return thumbnail;
};


/* the binary Great Common Divisor calculator */
function gcd (u, v) {
    if (u === v) return u;
    if (u === 0) return v;
    if (v === 0) return u;

    if (~u & 1)
    if (v & 1)
    return gcd(u >> 1, v);
    else
    return gcd(u >> 1, v >> 1) << 1;

    if (~v & 1) return gcd(u, v >> 1);

    if (u > v) return gcd((u - v) >> 1, v);

    return gcd((v - u) >> 1, u);
}

/* returns an array with the ratio */
function ratio (w, h) {
    var d = gcd(w,h);
    return [w/d, h/d];
}
