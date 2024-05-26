document.addEventListener( 'DOMContentLoaded', function () {
  var main = new Splide( '#main-carousel', {
    type                : 'slide',
    autoHeight          : true,
    rewind              : true,
    pagination          : false,
    arrows              : true,
  } );


  var thumbnails = new Splide( '#thumbnail-carousel', {
    fixedWidth  : 200,
    fixedHeight : 120,
    gap         : 10,
    rewind      : true,
    pagination  : false,
    arrows      : false,
    isNavigation: true,
    breakpoints : {
      600: {
        fixedWidth : 60,
        fixedHeight: 44,
      },
    },
  } );


  main.sync( thumbnails );
  main.mount();
  thumbnails.mount();
} );
