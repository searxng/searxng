/* SPDX-License-Identifier: AGPL-3.0-or-later */
(function (w, d, searxng) {
  'use strict';

  if (searxng.endpoint !== 'results') {
    return;
  }

  searxng.ready(function () {
    const formatUrl = (urlStr) => {
      const url = new URL(urlStr);
      return url.origin + url.pathname.split("/").join(" › ");
    }

    // client side hostname replace
    if (window.localStorage?.getItem("rewrites")) {
      const rewrites = window.localStorage.getItem("rewrites").split("\n");

      const applyAllRewrites = (url) => {
        for (let rewrite of rewrites) {

          // filter out blank lines
          if (!rewrite) continue;

          // we're dealing with user input here, hence all the regex logic
          // is done inside a try catch clause to avoid crashes due to wrong
          // usage by the end user
          try {
            const [pattern, replacement] = rewrite.split(":");
            const regExp = new RegExp(pattern);
            // if no replacement specified and the pattern found, all
            if (url.origin.match(regExp).length) {
              if (!replacement) return true;

              // replace the hostname of the url and skip any further patterns
              url.hostname = replacement;
              break;
            }
          } catch (exception) {
            // ignore malformed patterns and skip to the next one
            continue;
          }
        }

        return false;
      }

      // iterate over all visible results and replace the url if needed
      for (let element of document.querySelectorAll("article.result")) {
        const anchorElements = element.querySelectorAll("a");

        // iterate over all anchor elements with a 'href' and replace the
        // href if the pattern was found or completely remove it if no
        // replacement was provided by the user
        for (let anchorElement of anchorElements) {
          if (!anchorElement.href.trim()) continue;

          let newUrl = new URL(anchorElement.href);
          const shouldHide = applyAllRewrites(newUrl);
          if (shouldHide) {
            element.style.display = 'none';
            break;
          }
          anchorElement.href = newUrl.toString();
        }

        // update the url in the url preview wrapper
        const urlPreview = element.querySelector(".url_wrapper");
        if (urlPreview) {
          let url = new URL(urlPreview.href);
          applyAllRewrites(url);
          urlPreview.href = url;
          urlPreview.innerText = formatUrl(url);
        }
      }
    }
  });
})(window, document, window.searxng);
