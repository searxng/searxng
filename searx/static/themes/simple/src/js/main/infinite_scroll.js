/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */
/* global searxng */

searxng.ready(function () {
  'use strict';

  let w = window;
  let d = document;
  var root = d.compatMode == 'BackCompat' ? d.body : d.documentElement;

  function hasScrollbar () {
    return root.scrollHeight > root.clientHeight;
  }

  function loadNextPage () {
    var form = d.querySelector('#pagination form.next_page');
    if (!form) {
      return
    }
    var formData = new FormData(form);
    d.querySelector('#pagination').innerHTML = '<div class="loader"></div>';
    searxng.http('POST', d.querySelector('#search').getAttribute('action'), formData).then(
      function (response) {
        var scrollYBeforeInsert = w.scrollY;
        var nextPageDoc = new DOMParser().parseFromString(response, 'text/html');
        var articleList = nextPageDoc.querySelectorAll('#urls article');
        var paginationElement = nextPageDoc.querySelector('#pagination');
        var onlyImages = d.getElementById('results').classList.contains('only_template_images');
        d.querySelector('#pagination').remove();
        if (articleList.length > 0 && !onlyImages) {
          // do not add <hr> element when there are only images
          d.querySelector('#urls').appendChild(d.createElement('hr'));
        }
        articleList.forEach(articleElement => {
          d.querySelector('#urls').appendChild(articleElement);
        });
        searxng.image_thumbnail_layout.align();
        w.scrollTo(w.scrollX, scrollYBeforeInsert);
        if (paginationElement) {
          d.querySelector('#results').appendChild(paginationElement);
          if (!hasScrollbar()) {
            loadNextPage();
          }
        }
      }
    ).catch(
      function (err) {
        console.log(err);
        d.querySelector('#pagination').innerHTML = '<div class="dialog-error" role="alert"><div><p>' +
          searxng.translations.error_loading_next_page +
          '</p></div></div>';
      }
    )
  }

  function onScroll () {
    let clientRect = root.getBoundingClientRect();
    if (root.scrollHeight - root.scrollTop - clientRect.height  < 150) {
      loadNextPage();
    }
  }

  if (searxng.infinite_scroll) {
    d.getElementsByTagName('html')[0].classList.add('infinite_scroll')
    if (!hasScrollbar()) {
      loadNextPage();
    }
    d.addEventListener('scroll', onScroll, { passive: true });
  }

});
