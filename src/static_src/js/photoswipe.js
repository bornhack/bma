import PhotoSwipeLightbox from "/static/js/vendor/photoswipe-lightbox-v5.4.4.esm.min.js";
// https://github.com/dimsemenov/photoswipe-video-plugin
import PhotoSwipeVideoPlugin from '/static/js/vendor/photoswipe-video-plugin-v1.0.2.esm.min.js';
import PhotoSwipeDynamicCaption from '/static/js/vendor/photoswipe-dynamic-caption-plugin-v1.2.7.esm.js';
const lightbox = new PhotoSwipeLightbox({
    gallery: '#gallery',
    children: 'a.gallerya',
    pswpModule: () => import('/static/js/vendor/photoswipe-v5.4.4.esm.min.js')
});

const videoPlugin = new PhotoSwipeVideoPlugin(lightbox, {
    // options
});

const captionPlugin = new PhotoSwipeDynamicCaption(lightbox, {
  // Plugins options, for example:
  type: 'auto',
  captionContent: (slide) => {
    console.log(slide.data.element);
    return slide.data.element.parentElement.querySelector(".pswp-caption-content").innerHTML
  },
});

lightbox.init();
