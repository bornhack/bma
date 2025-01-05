{% load static %}

(async function(){
  // config (rendered serverside)
  const uuid = "{{ uuid }}";
  const host = "{{ host }}";
  const count = "{{ count }}";
  const photoswipe_main_loader = document.createElement('div');
  photoswipe_main_loader.id = "photoswipe-" + count + "-loader"
  photoswipe_main_loader.innerHTML = `<div class="spinner-grow" role="status"></div><span class="h3">Loading Gallery....</span>`;

  // custom error class
  class BmaNotFoundError extends Error {
    constructor(message) {
      super(message);
      this.name = "BmaNotFoundError";
    }
  }
  class BmaApiError extends Error {
    constructor(message) {
      super(message);
      this.name = "BmaApiError";
    }
  }
  class BmaPermissionError extends Error {
    constructor(message) {
      super(message);
      this.name = "BmaPermissionError";
    }
  }

  // A reference to the currently running script
  const bma_script = document.scripts[document.scripts.length - 1];
  bma_script.parentElement.insertBefore(photoswipe_main_loader, bma_script);

  // load photoswipe css and js, which in turn calls init() when it is done loading
  await loadPhotoswipe();

  async function loadPhotoswipe() {
    // load photoswipe JS
    const {lightbox} = await import(`${window.location.protocol}//${host}/widgets/photoswipe-module/${count}/${uuid}/`);

    // load photoswipe CSS
    let photoswipe_css = document.createElement( "link" );
    photoswipe_css.href = "//" + host + "{% static 'css/vendor/photoswipe-v5.4.4.css' %}";
    photoswipe_css.type = "text/css";
    photoswipe_css.rel = "stylesheet";
    photoswipe_css.media = "screen,print";
    document.head.appendChild(photoswipe_css);

    // load custom css
    let custom_css = document.createElement( "link" );
    custom_css.href = "//" + host + "{% static 'css/vendor/photoswipe-dynamic-caption-plugin-v1.2.7.css' %}";
    custom_css.type = "text/css";
    custom_css.rel = "stylesheet";
    custom_css.media = "screen,print";
    document.head.appendChild(custom_css);

    await init();
    lightbox.init();
  }

  async function getFileMetadata(file_uuid) {
    const response = fetch("//" + host + "/api/v1/json/files/" + file_uuid + "/", {mode: 'cors'})
    .then((x) => {
      if (!x.ok) {
        // handle non-2xx x code
        if (x.status === 404) {
          throw new BmaNotFoundError("File UUID " + file_uuid + " not found!");
        } else if (x.status === 403) {
          throw new BmaPermissionError("No permission for file UUID " + file_uuid + "!");
        } else {
          throw new BmaApiError("BMA API returned unexpected x code " + x.status);
        }
      }
      return x.json()
    })
    .then((x) => ({[file_uuid]: x['bma_response']}))
    .catch((response) => {
      console.log(response);
    });
    return response
  }

  async function getAlbumMetadata(album_uuid) {
    let result = {};
    const response = fetch("//" + host + "/api/v1/json/albums/" + album_uuid + "/", {mode: 'cors'})
      .then((response) => {
        if (!response.ok) {
          // handle non-2xx response code
          if (response.status === 404) {
            throw new BmaNotFoundError("Album UUID " + album_uuid + " not found!");
          } else if (response.status === 403) {
            throw new BmaPermissionError("No permission for album UUID " + album_uuid + "!");
          } else {
            throw new BmaApiError("BMA API returned unexpected response code " + response.status);
          }
        }
        return response.json();
      })
    .then((data) => data["bma_response"])
    return response;
  }

  /**
   * Render the source set
   * @param {object} metadata - file metadata record
   * @param {string} source - Download or Thumbnail sources
   * @param {string} aspect_ration - the required aspect ratio
   * @returns {string}
   */
  function PswpSourceSet(metadata, source, aspect_ratio) {
    let urls = metadata["links"][source][aspect_ratio];
    if (!urls) {
      console.log("Source set error", metadata, source, aspect_ratio);
      return "";
    }
    let srcset = "";
    for (const [size, url] of Object.entries(urls)) {
      const sizes = size.split("*");
      srcset = srcset + "//" + host + url + " " + sizes[0] + "w, ";
    }
    return srcset;
  }

  /**
   * Creates a photoswipe thumbnail caption
   * @param {object} record - file record
   * @returns {string}
   */
  function createThumbnailCaption(file) {
    let caption = `<div class="pswp-caption-content" data-bma-file-uuid="${file.uuid}">
  <p class="d-inline-block"><i class="${file.filetype_icon}"></i> <a href="//${host}/${file.links.html}"><b>${file.title}</b></a></p>`;

    if (file.description)
      caption += `<span class="d-inline-block me-3"><i class="fas fa-newspaper fa-fw"></i> ${file.description}</span>`;
    if (file.filetype === "image" && file.exif) {
      if (file.exif.Image) {
        if (file.exif.Image.Make && file.exif.Image.Model)
          caption += `<span class="d-inline-block me-3"><i class="fas fa-camera fa-fw" title="Camera"></i> ${file.exif.Image.Make} ${file.exif.Image.Model}</span>`;
      }
      if (file.exif.EXIF) {
        if (file.exif.EXIF.LensModel)
          caption += `<span class="d-inline-block me-3"><i class="fas fa-video fa-fw" title="Lens"></i> ${file.exif.EXIF.LensModel}</span>`
        if (file.exif.EXIF.FocalLength)
          caption += `<span class="d-inline-block me-3"><i class="fas fa-ruler-horizontal fa-fw" title="Focal Length"></i> ${file.exif.EXIF.FocalLength}mm</span>`;

        if (file.exif.EXIF.ExposureTime)
          caption += `<span class="d-inline-block me-3"><i class="fas fa-stopwatch fa-fw" title="Shutter speed"></i> ${file.exif.EXIF.ExposureTime} s</span>`;

        if (file.exif.EXIF.ISOSpeedRatings)
          caption += `<span class="d-inline-block me-3"><i class="fas fa-eye fa-fw" title="ISO"></i> ISO ${file.exif.EXIF.ISOSpeedRatings}</span>`;

        if (file.exif.EXIF.FNumber)
          caption += `<span class="d-inline-block me-3"><i class="fas fa-florin-sign fa-fw" title="Aperture/f-stop"></i> ${file.exif.EXIF.FNumber}</span>`;

        if (file.exif.EXIF.Orientation)
          caption += `<span class="d-inline-block me-3"><i class="fas fa-camera-rotate fa-fw" title="Image Orientation"></i> ${file.exif.EXIF.Orientation}</span>`;

        if (file.exif.EXIF.DateTimeOriginal) {
          caption += `<br><span class="d-inline-block me-3"><i class="fas fa-calendar fa-fw" title="Picture taken time"></i> ${file.exif.EXIF.DateTimeOriginal}</span>`;
        }

      }
    }
    caption += "</div>";
    return caption;
  }

  /**
   * Creates a photoswipe thumbnail
   * @param {object} record - file record
   * @returns {string}
   */
  function createThumbnailPswp(record) {
    let thumb = `<span class="d-inline-block mb-1">`;
    if (record.filetype === "image") {
      thumb += `<a class="gallery-${count}-${uuid} text-decoration-none" href="//${host}/${record.links.downloads.original}"
    data-bma-file-uuid="${record.uuid}"
    data-bma-file-orig-url="//${host}/${record.links.downloads.original}"
    data-pswp-type="image"
    data-pswp-width="${record.width}"
    data-pswp-height="${record.height}"
    data-pswp-srcset="${PswpSourceSet(record, "downloads", record["aspect_ratio"])}">
    <div class="image-hover zoom">
      <i class="fas fa-2x"></i>
      <img srcset="${PswpSourceSet(record, "thumbnails", "1")}" width="150" height="150" />
    </div>
</a>${createThumbnailCaption(record)}`;
    }
    else if (record.filetype === "video") {
      thumb += `<a class="gallery-${count}-${uuid} text-decoration-none" href="//${host}/${record.links.downloads.original}"
    data-bma-file-uuid="${record.uuid}"
    data-bma-file-orig-url="//${host}/${record.links.downloads.original}"
    data-pswp-type="video"
    data-pswp-width="1280"
    data-pswp-height="1024"
    <div class="image-hover zoom">
      <i class="fas fa-2x"></i>
      <img srcset="${PswpSourceSet(record, "thumbnails", "16/9")}" height="150" />
    </div>
</a>${createThumbnailCaption(record)}`;
    }
    else if (record.filetype === "audio") {
      thumb += `<a class="gallery-${count}-${uuid} text-decoration-none" href="//${host}/${record.links.downloads.original}"
    data-bma-file-uuid="${record.uuid}"
    data-bma-file-orig-url="//${host}/${record.links.downloads.original}"
    data-pswp-type="video"
    data-pswp-width="640"
    data-pswp-height="480"
    <div class="image-hover zoom">
      <i class="fas fa-2x"></i>
      <img srcset="${PswpSourceSet(record, "thumbnails", "1")}" height="150" width="150"/>
    </div>
</a>${createThumbnailCaption(record)}`;
    }
    else if (record.filetype === "document") {
      thumb += `<a class="gallery-${count}-${uuid} text-decoration-none" href="//${host}/${record.links.downloads.original}"
    data-bma-file-uuid="${record.uuid}"
    data-bma-file-orig-url="//${host}/${record.links.downloads.original}"
    data-pswp-type="document"
    data-pswp-width="1920"
    data-pswp-height="1080"
    <div class="image-hover zoom">
      <i class="fas fa-2x"></i>
      <img srcset="${PswpSourceSet(record, "thumbnails", "1")}" height="150" width="150"/>
    </div>
</a>${createThumbnailCaption(record)}`;
    } else {
      console.log("Filetype not found", record)
    }
    return thumb;
  }

  async function createPhotoswipe(files) {
    const photoswipe_main_div = document.createElement('div');

    // begin main photoswipe
    photoswipe_main_div.className = "row";
    photoswipe_main_div.innerHTML = `<div class="pswp-gallery" id="photoswipe-${count}-${uuid}-main">`;
    // begin thumbnail photoswipe
    // loop over files and add photoswipe slides
    for (const [_fileid, metadata] of Object.entries(files)) {
      if (metadata)
        photoswipe_main_div.querySelector("div").innerHTML += createThumbnailPswp(metadata);
      else {
        console.log("Missing metadata", count, _fileid, metadata)
        //let m = await getFileMetadata(_fileid);
        //photoswipe_main_div.querySelector("div").innerHTML += createThumbnailPswp(m[_fileid]);
      }
    };
    // closing divs and ul elements are added automatically,
    // just add the photoswipe to DOM right where the embed was made
    photoswipe_main_loader.remove();
    bma_script.parentElement.insertBefore(photoswipe_main_div, bma_script);
  }

  async function init() {
    // figure out which file(s) to show
    let files = {};

    // is this uuid a file?
    try {
      const metadata = await getFileMetadata(uuid);
      if (metadata)
        files[uuid] = metadata[uuid];
    } catch (error) {
      if (!error instanceof BmaNotFoundError) {
        // API returned an error other than 404
        console.error("BMA API returned an error: ", error);
        return;
      }
    }

    // is this uuid an album?
    if (!(uuid in files)) {
      // check if the uuid is an album
      try {
        const album = await getAlbumMetadata(uuid);
        for (const file of album["files"]) {
          metadata = await getFileMetadata(file);
          files[file] = metadata[file];
        }
      } catch (error) {
        // API returned an error
        console.error("BMA API returned an error: ", error);
        return;
      }
    }

    // ready
    await createPhotoswipe(files);
  }
})()
