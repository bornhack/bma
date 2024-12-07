// https://github.com/dimsemenov/PhotoSwipe
import PhotoSwipeLightbox from "/static/js/vendor/photoswipe-lightbox-v5.4.4.esm.min.js";

// https://github.com/dimsemenov/photoswipe-video-plugin
import PhotoSwipeVideoPlugin from '/static/js/vendor/photoswipe-video-plugin-v1.0.2.esm.min.js';

// https://github.com/dimsemenov/photoswipe-dynamic-caption-plugin
import PhotoSwipeDynamicCaption from '/static/js/vendor/photoswipe-dynamic-caption-plugin-v1.2.7.esm.js';

// https://github.com/junkfix/photoswipe-slideshow
import PhotoSwipeSlideshow from '/static/js/vendor/photoswipe-slideshow.21b9b68e9ffa5bbd370d57888ebf001dd08e36e2.esm.js';

// https://github.com/arnowelzel/photoswipe-auto-hide-ui
import PhotoSwipeAutoHideUI from '/static/js/vendor/photoswipe-auto-hide-ui.v1.0.1.esm.js';

// https://github.com/arnowelzel/photoswipe-fullscreen
import PhotoSwipeFullscreen from '/static/js/vendor/photoswipe-fullscreen.v1.0.5.esm.js';

///////////////////////////////////////////////////////////////////////////////

// initialize lightbox
const lightbox = new PhotoSwipeLightbox({
    gallery: '#gallery',
    children: 'a.gallerya',
    bgOpacity: 0.90,
    pswpModule: () => import('/static/js/vendor/photoswipe-v5.4.4.esm.min.js')
});

// enable videoplugin
const videoPlugin = new PhotoSwipeVideoPlugin(lightbox, {
    // no options for now
});

// enable captionplugin
const captionPlugin = new PhotoSwipeDynamicCaption(lightbox, {
  // Plugins options
  type: 'auto',
  captionContent: (slide) => {
    return slide.data.element.parentElement.querySelector("div.pswp-caption-content").innerHTML
  },
});

// slideshow plugin
const slideshowPlugin = new PhotoSwipeSlideshow(lightbox, {
  // Plugin options
  defaultDelayMs: 5000,
  progressBarPosition: 'bottom',
});

// autohideui plugin
const autoHideUI = new PhotoSwipeAutoHideUI(lightbox, {
  // Plugin options
  idleTime: 4000  // ms
});

// fullscreen plugin
const fullscreenPlugin = new PhotoSwipeFullscreen(lightbox);

///////////////////////////////////////////////////////////////////////////////
// bullets
lightbox.on('uiRegister', function() {
  lightbox.pswp.ui.registerElement({
    name: 'bulletsIndicator',
    className: 'pswp__bullets-indicator',
    appendTo: 'wrapper',
    onInit: (el, pswp) => {
      // skip bullets if there is only 1 file
      if (pswp.getNumItems() == 1) {
        return;
      };
      const bullets = [];
      let bullet;
      let prevIndex = -1;

      for (let i = 0; i < pswp.getNumItems(); i++) {
        bullet = document.createElement('div');
        bullet.className = 'pswp__bullet';
        bullet.onclick = (e) => {
          pswp.goTo(bullets.indexOf(e.target));
        };
        el.appendChild(bullet);
        bullets.push(bullet);
      }

      pswp.on('change', (a,) => {
        if (prevIndex >= 0) {
          bullets[prevIndex].classList.remove('pswp__bullet--active');
        }
        bullets[pswp.currIndex].classList.add('pswp__bullet--active');
        prevIndex = pswp.currIndex;
      });
    }
  });
});

///////////////////////////////////////////////////////////////////////////////
// add download button
lightbox.on('uiRegister', function() {
  lightbox.pswp.ui.registerElement({
    name: 'download-button',
    order: 8,
    isButton: true,
    tagName: 'a',
    html: {
      isCustomSVG: true,
      inner: '<path d="M20.5 14.3 17.1 18V10h-2.2v7.9l-3.4-3.6L10 16l6 6.1 6-6.1ZM23 23H9v2h14Z" id="pswp__icn-download"/>',
      outlineID: 'pswp__icn-download'
    },
    onInit: (el, pswp) => {
      el.setAttribute('download', '');
      el.setAttribute('rel', 'noopener');
      pswp.on('change', () => {
        el.href = pswp.currSlide.data.element.dataset.bmaFileOrigUrl;
        el.title = "Download original";
      });
    }
  });
});

///////////////////////////////////////////////////////////////////////////////
// update url with a hash/anchor with the uuid of the current slide
lightbox.on('contentActivate', ({ content }) => {
  history.replaceState(undefined, '', "#lightbox="+content.data.element.dataset.bmaFileUuid)
});
// remove anchor when lightbox closes
lightbox.on('close', () => {
  history.replaceState(undefined, '', window.location.pathname + window.location.search);
});

// initialise the lightbox
lightbox.init();

// open lightbox on page load?
if (location.hash && location.hash.substring(0, 10) == "#lightbox=") {
    let slide = document.querySelector("a.gallerya[data-bma-file-uuid='" + location.hash.substring(10) + "']");
    slide.click();
}
