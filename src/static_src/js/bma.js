jQuery(document).ready(function () {
    // get the wrapper div
    pw = document.getElementById("preview-wrapper");

    // get the preview templates
    pt = document.getElementById("preview-template");

    // bind change event and make an initial trigger call to it
    $('#id_files').bind('change', UpdateFiles);
    $('#id_files').trigger("change");
});

// use global var for the formData objects
var formdatas = [];

async function UpdateFiles(e) {
    // the file picker was changed
    document.getElementById("btnupload").disabled=true;
    var filesArr = Array.prototype.slice.call(e.target.files);
    // loop over chosen files and hash each
    // TODO: maybe this needs to be batched to some sensible number of parallels
    promises = [];
    filesArr.forEach(function (f, index) {
        // calculate file hash
        promises.push(ReadDigestFile(f, index));
    });
    // wait until all hashes have completed (or failed)
    await Promise.allSettled(promises);
    console.log("done, we now have " + formdatas.length + " formdatas");
    // clear the filepicker
    e.target.value = "";
    // update the previews
    UpdatePreviews(formdatas);

    // previews might still be loading but maybe the upload is ready to be submitted
    // show upload button if required fields are filled
    let select = document.getElementById("id_license");
    let license = select.options[select.selectedIndex].value;
    let attribution = document.getElementById("id_attribution").value;
    if (license && attribution && formdatas.length) {
        document.getElementById("btnupload").disabled=false;
    };
}

async function digestDone(f, index, digest) {
    // hashing done, have we seen this file already?
    try {
        formdatas.forEach(fd => {
            if (digest == fd.digest) {
                console.log("the file " + digest + " has been seen before, skipping " + f.name);
                throw "duplicate";
            };
        });
    } catch (err) {
        // either a duplicate was found or another error occurred, skip this file
        reject;
    }
    // create formData object and add to formadatas
    console.log("adding " + f.name + " to formdatas");
    let formData = new FormData();
    formData.append("f", f);
    formData.filename=f.name;
    formData.digest=digest;
    formdatas.push(formData);
    console.log("file " + f.name + " with hash " + digest + " has been added to formdatas");
    resolve();
}

async function ReadDigestFile(f, index) {
    // resolve to a sha256 of the file
    console.log("ReadDigestFile called for " + f.name);
    return new Promise((resolve, reject) => {
        // initiate filereader and define onload and error handler
        var reader = new FileReader();
        reader.onload = function(e) {
            crypto.subtle.digest('SHA-256', e.target.result).then(hashBuffer => {
                // convert digest to hex string
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                const digest = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
                console.log("calling digestDone with digest " + digest);
                // return the promise from digestDone so UpdateFiles() knows when were done
                resolve(digestDone(f, index, digest));
            }).catch(ex => console.error(ex));
        };
        reader.onerror = function(err) {
            throw "Failed to read file for hashing: " + err;
        }
        // read the file
        reader.readAsArrayBuffer(f);
    });
}

async function UpdatePreviews(formdatas) {
    // loop over formdatas to show thumbnails
    formdatas.forEach(function (fd, index) {
        var f = fd.get('f');
        // only create a preview div if we dont already have one for this file
        for (const div of pw.getElementsByClassName("preview")) {
            if(div.getAttribute("data-digest") == fd.digest) {
                // we already have a preview of this file, skip it
                return;
            };
        }

        // clone the preview template
        let clone = pt.content.cloneNode(true);
        clone.querySelector(".preview").setAttribute("data-digest", fd.digest);
        clone.querySelector(".card-title").innerHTML = f.name;
        // add the preview div to the wrapper div
        pw.append(clone);
        // only create previews for images for now
        if (f.type.match('image.*')) {
            // initiate the filereader and attach onload for the thumbnail
            UpdateStatus(fd.digest, "spinner", "Creating thumbnail...");
            var reader = new FileReader();
            reader.onload = function (e) {
                // get the image
                var originalImage = new Image();
                originalImage.src = e.target.result;
                // when the image is done loading generate the thumbnail
                originalImage.addEventListener("load", function () {
                    var thumbnailImage = createThumbnail(originalImage);
                    thumbnailImage.className = "card-img-top";
                    div = pw.querySelector('[data-digest="' + fd.digest + '"]');
                    div.querySelector(".card").prepend(thumbnailImage);
                    div.querySelector(".card-text").innerHTML = "Image is " + originalImage.width + " x " + originalImage.height + " pixels (aspect ratio " + ratio(originalImage.width, originalImage.height).join(":") + ")<br>File size " + f.size.toLocaleString() + " bytes";

                    UpdateStatus(fd.digest, "info", "Ready for upload");
                });
            }
            // this triggers the onload event when done
            //clone.querySelector(".card-footer")
            reader.readAsDataURL(f);
        } else {
            // not an image, no fancy preview for now
            UpdateStatus(fd.digest, "info", "Ready for upload");
        };
    });
}

async function UpdateStatus(digest, icon, message) {
    console.log("updating status for file " + digest + " to icon " + icon + " with message: " + message);
    // update the status message in the footer of the preview div
    let footer = pw.querySelector('[data-digest="' + digest + '"]').querySelector(".card-footer");
    footer.querySelectorAll("i").forEach((i) => { i.classList.add("d-none"); });
    footer.querySelector(".fa-" + icon).classList.remove("d-none");
    footer.querySelector(".message").innerHTML = message;
}

async function uploadFiles() {
    console.log("inside uploadFiles()");
    // disable upload button
    document.getElementById("btnupload").setAttribute("disabled", "");
    let previews = pw.querySelectorAll(".preview");
    console.log("showing spinners ...");
    // show spinners
    previews.forEach((preview) => {
        if (preview.dataset.digest) {
            UpdateStatus(preview.dataset.digest, "spinner", "Uploading...");
        };
    });

    console.log("creating metadata object...");
    // create file metadata object from the form fields
    let metadata = {};
    let license = document.getElementById("id_license");
    metadata.license = license.options[license.selectedIndex].value;
    metadata.attribution = document.getElementById("id_attribution").value;

    // loop over formdatas, add metadata to each, and submit each
    // TODO: batch into groups of some reasonable size
    console.log("looping over formdatas ...");
    for (let fd of formdatas) {
        console.log("adding digest to metadata ...");
        metadata.digest = fd.digest;
        console.log("adding metadata to formdata ...");
        fd.append("metadata", JSON.stringify(metadata));
        console.log("calling uploadFile ...");
        try {
            response = await uploadFile(fd);
            UpdateStatus(fd.digest, "check", "Upload OK - file UUID " + response.uuid);
        } catch (error) {
            UpdateStatus(fd.digest, "exclamation-times", "Upload error: " + error);
        }
    };
}

async function uploadFile(fd) {
    console.log("uploading " + fd.digest + "...");
    response = await fetch('/api/v1/json/files/upload/', {
        method: "POST",
        headers: {
            'X-CSRFToken': document.getElementsByName("csrfmiddlewaretoken")[0].value
        },
        body: fd
    })
    if (!response.ok) {
        UpdateStatus(fd.digest, "exclamation-times", "Upload error: response status " + response.status);
        throw new Error("Response status " + response.status);
    }
    return response.json();
}

var thumbnailMaxWidth = 400;
var thumbnailMaxHeight = 400;

function createThumbnail(image) {
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
