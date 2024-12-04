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
    return slide.data.element.parentElement.querySelector(".pswp-caption-content").innerHTML
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

// disco!
lightbox.init();
