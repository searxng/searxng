/* SPDX-License-Identifier: AGPL-3.0-or-later */
(function(w, d, searxng) {
  'use strict';

  searxng.ready(function() {
    searxng.image_thumbnail_layout = new searxng.ImageLayout('#urls', '#urls .result-images', 'img.image_thumbnail', 10, 200);
    searxng.image_thumbnail_layout.watch();

    searxng.on('.btn-collapse', 'click', function() {
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

    searxng.on('.media-loader', 'click', function() {
      var target = this.getAttribute('data-target');
      var iframe_load = d.querySelector(target + ' > iframe');
      var srctest = iframe_load.getAttribute('src');
      if (srctest === null || srctest === undefined || srctest === false) {
        iframe_load.setAttribute('src', iframe_load.getAttribute('data-src'));
      }
    });

    w.addEventListener('scroll', function() {
      var e = d.getElementById('backToTop'),
      scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
      if (e !== null) {
        if (scrollTop >= 200) {
          e.style.opacity = 1;
        } else {
          e.style.opacity = 0;
        }
      }
    });

  });

})(window, document, window.searxng);
