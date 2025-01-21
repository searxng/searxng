/* SPDX-License-Identifier: AGPL-3.0-or-later */
(function (w, d, searxng) {
  'use strict';

  if (searxng.endpoint !== 'results') {
    return;
  }

  searxng.ready(function () {
    d.querySelectorAll('#urls img').forEach(
      img =>
        img.addEventListener(
          'error', () => {
            // console.log("ERROR can't load: " + img.src);
            img.src = window.searxng.settings.theme_static_path + "/img/img_load_error.svg";
          },
          {once: true}
        ));

    if (d.querySelector('#search_url button#copy_url')) {
      d.querySelector('#search_url button#copy_url').style.display = "block";
    }

    searxng.on('.btn-collapse', 'click', function () {
      var btnLabelCollapsed = this.getAttribute('data-btn-text-collapsed');
      var btnLabelNotCollapsed = this.getAttribute('data-btn-text-not-collapsed');
      var target = this.getAttribute('data-target');
      var targetElement = d.querySelector(target);
      var html = this.innerHTML;
      if (this.classList.contains('collapsed')) {
        html = html.replace(btnLabelCollapsed, btnLabelNotCollapsed);
      } else {
        html = html.replace(btnLabelNotCollapsed, btnLabelCollapsed);
      }
      this.innerHTML = html;
      this.classList.toggle('collapsed');
      targetElement.classList.toggle('invisible');
    });

    searxng.on('.media-loader', 'click', function () {
      var target = this.getAttribute('data-target');
      var iframe_load = d.querySelector(target + ' > iframe');
      var srctest = iframe_load.getAttribute('src');
      if (srctest === null || srctest === undefined || srctest === false) {
        iframe_load.setAttribute('src', iframe_load.getAttribute('data-src'));
      }
    });

    searxng.on('#copy_url', 'click', function () {
      var target = this.parentElement.querySelector('pre');
      navigator.clipboard.writeText(target.innerText);
      this.innerText = this.dataset.copiedText;
    });

    // searxng.selectImage (gallery)
    // -----------------------------

    // setTimeout() ID, needed to cancel *last* loadImage
    let imgTimeoutID;

    // progress spinner, while an image is loading
    const imgLoaderSpinner = d.createElement('div');
    imgLoaderSpinner.classList.add('loader');

    // singleton image object, which is used for all loading processes of a
    // detailed image
    const imgLoader = new Image();

    const loadImage = (imgSrc, onSuccess) => {
      // if defered image load exists, stop defered task.
      if (imgTimeoutID) clearTimeout(imgTimeoutID);

      // defer load of the detail image for 1 sec
      imgTimeoutID = setTimeout(() => {
        imgLoader.src = imgSrc;
      }, 1000);

      // set handlers in the on-properties
      imgLoader.onload = () => {
        onSuccess();
        imgLoaderSpinner.remove();
      };
      imgLoader.onerror = () => {
        imgLoaderSpinner.remove();
      };
    };

    searxng.selectImage = (resultElement) => {

      // add a class that can be evaluated in the CSS and indicates that the
      // detail view is open
      d.getElementById('results').classList.add('image-detail-open');

      // add a hash to the browser history so that pressing back doesn't return
      // to the previous page this allows us to dismiss the image details on
      // pressing the back button on mobile devices
      window.location.hash = '#image-viewer';

      searxng.scrollPageToSelected();

      // if there is none element given by the caller, stop here
      if (!resultElement) return;

      // find <img> object in the element, if there is none, stop here.
      const img = resultElement.querySelector('.result-images-source img');
      if (!img) return;

      // <img src="" data-src="http://example.org/image.jpg">
      const src = img.getAttribute('data-src');

      // already loaded high-res image or no high-res image available
      if (!src) return;

      // use the image thumbnail until the image is fully loaded
      const thumbnail = resultElement.querySelector('.image_thumbnail');
      img.src = thumbnail.src;

      // show a progress spinner
      const detailElement = resultElement.querySelector('.detail');
      detailElement.appendChild(imgLoaderSpinner);

      // load full size image in background
      loadImage(src, () => {
        // after the singelton loadImage has loaded the detail image into the
        // cache, it can be used in the origin <img> as src property.
        img.src = src;
        img.removeAttribute('data-src');
      });
    };

    searxng.closeDetail = function () {
      d.getElementById('results').classList.remove('image-detail-open');
      // remove #image-viewer hash from url by navigating back
      if (window.location.hash == '#image-viewer') window.history.back();
      searxng.scrollPageToSelected();
    };
    searxng.on('.result-detail-close', 'click', e => {
      e.preventDefault();
      searxng.closeDetail();
    });
    searxng.on('.result-detail-previous', 'click', e => {
      e.preventDefault();
      searxng.selectPrevious(false);
    });
    searxng.on('.result-detail-next', 'click', e => {
      e.preventDefault();
      searxng.selectNext(false);
    });

    // listen for the back button to be pressed and dismiss the image details when called
    window.addEventListener('hashchange', () => {
      if (window.location.hash != '#image-viewer') searxng.closeDetail();
    });

    d.querySelectorAll('.swipe-horizontal').forEach(
      obj => {
        obj.addEventListener('swiped-left', function () {
          searxng.selectNext(false);
        });
        obj.addEventListener('swiped-right', function () {
          searxng.selectPrevious(false);
        });
      }
    );

    w.addEventListener('scroll', function () {
      var e = d.getElementById('backToTop'),
        scrollTop = document.documentElement.scrollTop || document.body.scrollTop,
        results = d.getElementById('results');
      if (e !== null) {
        if (scrollTop >= 100) {
          results.classList.add('scrolling');
        } else {
          results.classList.remove('scrolling');
        }
      }
    }, true);

  });

})(window, document, window.searxng);
