// SPDX-License-Identifier: AGPL-3.0-or-later

import "../../../node_modules/swiped-events/src/swiped-events.js";
import { listen, mutable, settings } from "../toolkit.ts";
import { assertElement } from "../util/assertElement.ts";

let imgTimeoutID: number;

const imageLoader = (resultElement: HTMLElement): void => {
  if (imgTimeoutID) clearTimeout(imgTimeoutID);

  const imgElement = resultElement.querySelector<HTMLImageElement>(".result-images-source img");
  if (!imgElement) return;

  // use thumbnail until full image loads
  const thumbnail = resultElement.querySelector<HTMLImageElement>(".image_thumbnail");
  if (thumbnail) {
    if (thumbnail.src === `${settings.theme_static_path}/img/img_load_error.svg`) return;

    imgElement.onerror = (): void => {
      imgElement.src = thumbnail.src;
    };

    imgElement.src = thumbnail.src;
  }

  const imgSource = imgElement.getAttribute("data-src");
  if (!imgSource) return;

  // unsafe nodejs specific, cast to https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout#return_value
  // https://github.com/searxng/searxng/pull/5073#discussion_r2265767231
  imgTimeoutID = setTimeout(() => {
    imgElement.src = imgSource;
    imgElement.removeAttribute("data-src");
  }, 1000) as unknown as number;
};

const imageThumbnails: NodeListOf<HTMLImageElement> =
  document.querySelectorAll<HTMLImageElement>("#urls img.image_thumbnail");
for (const thumbnail of imageThumbnails) {
  if (thumbnail.complete && thumbnail.naturalWidth === 0) {
    thumbnail.src = `${settings.theme_static_path}/img/img_load_error.svg`;
  }

  thumbnail.onerror = (): void => {
    thumbnail.src = `${settings.theme_static_path}/img/img_load_error.svg`;
  };
}

const copyUrlButton: HTMLButtonElement | null =
  document.querySelector<HTMLButtonElement>("#search_url button#copy_url");
copyUrlButton?.style.setProperty("display", "block");

mutable.selectImage = (resultElement: HTMLElement): void => {
  // add a class that can be evaluated in the CSS and indicates that the
  // detail view is open
  const resultsElement = document.getElementById("results");
  resultsElement?.classList.add("image-detail-open");

  // add a hash to the browser history so that pressing back doesn't return
  // to the previous page this allows us to dismiss the image details on
  // pressing the back button on mobile devices
  window.location.hash = "#image-viewer";

  mutable.scrollPageToSelected?.();

  // if there is no element given by the caller, stop here
  if (!resultElement) return;

  imageLoader(resultElement);
};

mutable.closeDetail = (): void => {
  const resultsElement = document.getElementById("results");
  resultsElement?.classList.remove("image-detail-open");

  // remove #image-viewer hash from url by navigating back
  if (window.location.hash === "#image-viewer") {
    window.history.back();
  }

  mutable.scrollPageToSelected?.();
};

listen("click", ".btn-collapse", function (this: HTMLElement) {
  const btnLabelCollapsed = this.getAttribute("data-btn-text-collapsed");
  const btnLabelNotCollapsed = this.getAttribute("data-btn-text-not-collapsed");
  const target = this.getAttribute("data-target");

  if (!(target && btnLabelCollapsed && btnLabelNotCollapsed)) return;

  const targetElement = document.querySelector<HTMLElement>(target);
  assertElement(targetElement);

  const isCollapsed = this.classList.contains("collapsed");
  const newLabel = isCollapsed ? btnLabelNotCollapsed : btnLabelCollapsed;
  const oldLabel = isCollapsed ? btnLabelCollapsed : btnLabelNotCollapsed;

  this.innerHTML = this.innerHTML.replace(oldLabel, newLabel);
  this.classList.toggle("collapsed");

  targetElement.classList.toggle("invisible");
});

listen("click", ".media-loader", function (this: HTMLElement) {
  const target = this.getAttribute("data-target");
  if (!target) return;

  const iframeLoad = document.querySelector<HTMLIFrameElement>(`${target} > iframe`);
  assertElement(iframeLoad);

  const srctest = iframeLoad.getAttribute("src");
  if (!srctest) {
    const dataSrc = iframeLoad.getAttribute("data-src");
    if (dataSrc) {
      iframeLoad.setAttribute("src", dataSrc);
    }
  }
});

listen("click", "#copy_url", async function (this: HTMLElement) {
  const target = this.parentElement?.querySelector<HTMLPreElement>("pre");
  assertElement(target);

  if (window.isSecureContext) {
    await navigator.clipboard.writeText(target.innerText);
  } else {
    const selection = window.getSelection();
    if (selection) {
      const range = document.createRange();
      range.selectNodeContents(target);
      selection.removeAllRanges();
      selection.addRange(range);
      document.execCommand("copy");
    }
  }

  if (this.dataset.copiedText) {
    this.innerText = this.dataset.copiedText;
  }
});

listen("click", ".result-detail-close", (event: Event) => {
  event.preventDefault();
  mutable.closeDetail?.();
});

listen("click", ".result-detail-previous", (event: Event) => {
  event.preventDefault();
  mutable.selectPrevious?.(false);
});

listen("click", ".result-detail-next", (event: Event) => {
  event.preventDefault();
  mutable.selectNext?.(false);
});

// listen for the back button to be pressed and dismiss the image details when called
window.addEventListener("hashchange", () => {
  if (window.location.hash !== "#image-viewer") {
    mutable.closeDetail?.();
  }
});

const swipeHorizontal: NodeListOf<HTMLElement> = document.querySelectorAll<HTMLElement>(".swipe-horizontal");
for (const element of swipeHorizontal) {
  listen("swiped-left", element, () => {
    mutable.selectNext?.(false);
  });

  listen("swiped-right", element, () => {
    mutable.selectPrevious?.(false);
  });
}

window.addEventListener(
  "scroll",
  () => {
    const backToTopElement = document.getElementById("backToTop");
    const resultsElement = document.getElementById("results");

    if (backToTopElement && resultsElement) {
      const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
      const isScrolling = scrollTop >= 100;
      resultsElement.classList.toggle("scrolling", isScrolling);
    }
  },
  true
);
