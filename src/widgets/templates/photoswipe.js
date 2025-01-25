{% load static %}

(async function(){
  {% include "includes/base.js" %}

  // load photoswipe css and js, which in turn calls init() when it is done loading
  await loadPhotoswipe();

  /**
   * Load PhotoSwipe
   */
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

    // load photoswipe widget CSS
    let photoswipe_widget_css = document.createElement( "link" );
    photoswipe_widget_css.href = "//" + host + "{% static 'css/photoswipe-widget.css' %}";
    photoswipe_widget_css.type = "text/css";
    photoswipe_widget_css.rel = "stylesheet";
    photoswipe_widget_css.media = "screen,print";
    document.head.appendChild(photoswipe_widget_css);

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
  <span class="d-inline-block me-3"><i class="${file.filetype_icon}"></i> <a href="//${host}/${file.links.html}"><b>${file.title}</b></a></span>`;

    caption += `<span class="d-inline-block me-3"><i class="fas fa-user fa-fw"></i> ${file.attribution}</span>`;
    caption += `<span class="d-inline-block me-3">${createLicenseIcon(file.license)} ${file.license_name}</span>`;
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
          caption += `<span class="d-inline-block me-3"><i class="fas fa-calendar fa-fw" title="Picture taken time"></i> ${file.exif.EXIF.DateTimeOriginal}</span>`;
        }

      }
    }
    caption += "</div>";
    return caption;
  }

  /**
   * Creates license icon
   * @param {string} license - License name
   * @returns {string}
   */
  function createLicenseIcon(license) {
    switch(license) {
      case "CC_ZERO_1_0":
        return '<i class="fa-brands fa-creative-commons-zero"></i>'; 
      case "CC_BY_4_0":
        return '<i class="fa-brands fa-creative-commons-by"></i>'; 
      case "CC_BY_SA_4_0":
        return '<i class="fa-brands fa-creative-commons-sa"></i>'; 
      default:
        return license; 
    }
  }

  /**
   * Creates a photoswipe thumbnail
   * @param {object} record - file record
   * @returns {string}
   */
  function createThumbnailPswp(record) {
    let thumb = `<span class="d-inline-block m-1">`;
    if (record.filetype === "image") {
      thumb += `<a class="gallery-${count}-${uuid} text-decoration-none" href="//${host}/${record.links.downloads.original}"
    data-bma-file-uuid="${record.uuid}"
    data-bma-file-orig-url="//${host}/${record.links.downloads.original}"
    data-pswp-type="image"
    data-pswp-width="${record.width}"
    data-pswp-height="${record.height}"
    data-pswp-srcset="${PswpSourceSet(record, "downloads", record["aspect_ratio"])}"
    title="${record.title}"
    >
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
    title="${record.title}"
    >
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
    title="${record.title}"
    >
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
    title="${record.title}"
    >
    <div class="image-hover zoom">
      <i class="fas fa-2x"></i>
      <img srcset="${PswpSourceSet(record, "thumbnails", "1")}" height="150" width="150"/>
    </div>
</a>${createThumbnailCaption(record)}`;
    } else {
      console.log("Filetype not found", record)
    }
    thumb += `<div class="d-flex gray-100 shadow bg-gradient justify-content-between fw-lighter ps-1 d-inline-block">
    <span class="d-inline-block text-truncate photoswipe-attribution-size" title="${record.attribution}">
      <a class="text-truncate text-reset" href="//${host}/${record.links.html}">${record.attribution}</a>
    </span><span title="${record.license_name}">
      <a class="text-reset" href="${record.license_url}">${createLicenseIcon(record.license)}</a>
    </span></div>`;
    thumb += "</span>"
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
    };
    //Show message if there are no files to display
    if (Object.entries(files).length === 0)
      photoswipe_main_div.querySelector("div").innerHTML = "Sorry no files to display";
    // closing divs and ul elements are added automatically,
    // just add the photoswipe to DOM right where the embed was made
    main_loader.remove();
    bma_script.parentElement.insertBefore(photoswipe_main_div, bma_script);
  }

  async function init() {
    // figure out which file(s) to show
    const files = JSON.parse(templateFiles).reduce((acc, t) => {
      acc[t.uuid] = t;
      return acc;
    }, {});
    await createPhotoswipe(files);
  }
})()
