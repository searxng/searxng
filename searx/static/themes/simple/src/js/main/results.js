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
      searxng.scrollPageToSelected();
    }

    searxng.closeDetail = function (e) {
      d.getElementById('results').classList.remove('image-detail-open');
      searxng.scrollPageToSelected();
    }
    searxng.on('.result-detail-close', 'click', e => {
      e.preventDefault();
      searxng.closeDetail();
    });
    searxng.on('.result-detail-previous', 'click', e => {
      e.preventDefault();
      searxng.selectPrevious(false)
    });
    searxng.on('.result-detail-next', 'click', e => {
      e.preventDefault();
      searxng.selectNext(false);
    });

    const searchHeader = d.getElementById('search');
    const searchFilters = d.querySelector('.search_filters')
    const searchHeaderTopHide = 155
    let lastScrollY = 0;
    w.addEventListener('scroll', function () {
      const currentScrollY = w.scrollY;
      if (w.scrollY <= 0) {
        searchFilters.classList.remove('search_filters_hide')
      }
      if (currentScrollY > lastScrollY || (currentScrollY > lastScrollY && currentScrollY < 300 && searchHeader.style.top !== '0px')) {
        // searchHeader.style.top = `-${searchHeaderTopHide}px`;
        searchHeader.className = 'search_hide'
        if (w.scrollY <= 0) {
          searchFilters.classList.remove('search_filters_hide')
          // searchFilters.style.height = '35px'
        } else {
          searchFilters.classList.add('search_filters_hide')
          // searchFilters.style.height = '0'
        }
      } else {
        searchHeader.className = 'search_show'
        // searchHeader.style.top = '-53px';
      }
      lastScrollY = currentScrollY;

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
