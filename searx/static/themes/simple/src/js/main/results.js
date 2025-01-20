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

    const isMobile = screen.orientation.type.startsWith('portrait');
    searxng.selectImage = function (resultElement) {
      /* eslint no-unused-vars: 0 */
      if (resultElement) {
        // load full size image in background
        const imgElement = resultElement.querySelector('.result-images-source img');
        const thumbnailElement = resultElement.querySelector('.image_thumbnail');
        const detailElement = resultElement.querySelector('.detail');
        if (imgElement) {
          const imgSrc = imgElement.getAttribute('data-src');
          if (imgSrc) {
            const loader = d.createElement('div');
            const imgLoader = new Image();

            loader.classList.add('loader');
            detailElement.appendChild(loader);

            imgLoader.onload = e => {
              imgElement.src = imgSrc;
              loader.remove();
            };
            imgLoader.onerror = e => {
              loader.remove();
            };
            imgLoader.src = imgSrc;
            imgElement.src = thumbnailElement.src;
            imgElement.removeAttribute('data-src');
          }
        }
      }
      d.getElementById('results').classList.add('image-detail-open');

      // add a hash to the browser history so that pressing back doesn't return to the previous page
      // this allows us to dismiss the image details on pressing the back button on mobile devices
      window.location.hash = '#image-viewer';

      searxng.scrollPageToSelected();
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
        obj.addEventListener('swiped-left', function (e) {
          searxng.selectNext(false);
        });
        obj.addEventListener('swiped-right', function (e) {
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
