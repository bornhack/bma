document.addEventListener( 'DOMContentLoaded', function () {
  var main = new Splide( '#main-carousel', {
    type                : 'slide',
    autoHeight          : true,
    rewind              : true,
    pagination          : false,
    arrows              : true,
  } );

  var thumbnails = new Splide( '#thumbnail-carousel', {
    //fixedWidth  : 100,
    //fixedHeight : 112,
    height      : "10vh",
    //width       : "100%",
    autoWidth   : true,
    focus       : 'center',
    gap         : 10,
    rewind      : true,
    pagination  : false,
    arrows      : true,
    isNavigation: true,
  } );

  var metadata = new Splide( '#metadata-carousel', {
    rewind      : true,
    pagination  : false,
    arrows      : false,
    isNavigation: false,
    perPage     : 1,
  } );

  main.sync( thumbnails );
  main.sync( metadata );
  main.mount();
  thumbnails.mount();
  metadata.mount();
} );
