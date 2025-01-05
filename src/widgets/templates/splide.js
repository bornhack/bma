{% load static %}

(async function(){
  {% include "includes/base.js" %}

  // load splide css and js, which in turn calls init() when it is done loading
  loadSplide();

  async function loadSplide() {
    // load splide JS
    let splide_script = document.createElement('script');
    splide_script.src = '//' + host + '{% static "js/vendor/splide-v4.1.3.min.js" %}';
    splide_script.addEventListener("load", () => {
      init();
    });
    document.head.appendChild(splide_script);

    // load splide CSS
    let splide_css = document.createElement( "link" );
    splide_css.href = "//" + host + "{% static 'css/vendor/splide-sea-green-v4.1.3.min.css' %}";
    splide_css.type = "text/css";
    splide_css.rel = "stylesheet";
    splide_css.media = "screen,print";
    document.head.appendChild(splide_css);

    // load custom css
    let custom_css = document.createElement( "link" );
    custom_css.href = "//" + host + "{% static 'css/splide-custom.css' %}";
    custom_css.type = "text/css";
    custom_css.rel = "stylesheet";
    custom_css.media = "screen,print";
    document.head.appendChild(custom_css);
  }

  async function createSplide(files) {
    const splide_main_div = document.createElement('div');
    const splide_thumb_ul = document.createElement("ul");
    const splide_main_id = "splide-" + count + "-main";
    const splide_thumb_id = "splide-" + count + "-thumb";

    // begin main splide
    splide_main_div.innerHTML = '<div class="splide" id="' + splide_main_id + '" role="group"><div class="splide__track"><ul class="splide__list">';
    // begin thumbnail splide
    splide_thumb_ul.setAttribute("id", splide_thumb_id);
    splide_thumb_ul.className = "splide-thumbnails";
    // loop over files and add splide slides
    for (const [fileid, metadata] of Object.entries(files)) {
      // get URLs from metadata
      let urls = metadata["links"]["downloads"][metadata["aspect_ratio"]];
      let srcset = "";
      for (const [size, url] of Object.entries(urls)) {
        const sizes = size.split("*");
        srcset = srcset + "//" + host + url + " " + sizes[0] + "w, ";
      }
      let thumburl = metadata["links"]["thumbnails"]["1"]["200*200"];
      // create metadata table
      let tbl = '<table class="table">';
      tbl += '<tr><th>Title</th><td>' + metadata["title"] + '</td></tr>';
      tbl += '<tr><th>Author</th><td>' + metadata["attribution"] + '</td></tr>';
      tbl += '<tr><th>Source</th><td><a href="//' + host + metadata["source"] + '" target="_blank">' + host + metadata["source"] + '</a></td></tr>';
      tbl += '<tr><th>License</th><td><a href="' + metadata["license_url"] + '" target="_blank">' + metadata["license_name"] + '</a></td></tr>';
      tbl += '<tr><th>Description</th><td>' + metadata["description"] + '</td></tr>';
      tbl += '</table>';

      // add slide li to splide__list ul
      splide_main_div.querySelector("div > div > ul").innerHTML += '<li class="splide__slide"><div class="splide-center"><img srcset="' + srcset + '" sizes="100wv"></div><div>' + tbl + '</div></li>';
      // add thumbnail for this file
      splide_thumb_ul.innerHTML += '<li class="splide-thumbnail"><img src="//' + host + thumburl + '"></li>';
    };
    // closing divs and ul elements are added automatically,
    // just add the splide to DOM right where the embed was made
    main_loader.remove();
    bma_script.parentElement.insertBefore(splide_main_div, bma_script);
    bma_script.parentElement.insertBefore(splide_thumb_ul, bma_script);

    // create main splide
    var splide = new Splide( '#' + splide_main_id, {
      pagination: false,
    })

    async function initThumbnail( thumbnail, index ) {
      thumbnail.addEventListener( 'click', function () {
        splide.go( index );
      } );
    }

    // get thumbnails
    thumbnails = splide_thumb_ul.querySelectorAll("li");
    for ( var i = 0; i < thumbnails.length; i++ ) {
      initThumbnail( thumbnails[ i ], i );
    }
    var current; // Keeps the current thumbnail

    splide.on( 'mounted move', function () {
      if ( current ) {
        current.classList.remove( 'is-active' );
      }

      // Splide#index returns the latest slide index:
      var thumbnail = thumbnails[ splide.index ];

      if ( thumbnail ) {
        thumbnail.classList.add( 'is-active' );
        current = thumbnail;
      }
    });

    // ready to mount
    splide.mount();

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
          if (metadata)
            files[file] = metadata[file];
        }
      } catch (error) {
        // API returned an error
        console.error("BMA API returned an error: ", error);
        return;
      }
    }

    // ready
    await createSplide(files);
  }
})()
