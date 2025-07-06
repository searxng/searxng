import "../../../node_modules/swiped-events/src/swiped-events.js";
import { assertElement, searxng } from "./00_toolkit.ts";

const loadImage = (imgSrc: string, onSuccess: () => void): void => {
  // singleton image object, which is used for all loading processes of a detailed image
  const imgLoader = new Image();

  // set handlers in the on-properties
  imgLoader.onload = () => {
    onSuccess();
  };

  imgLoader.src = imgSrc;
};

searxng.ready(
  () => {
    const imageThumbnails = document.querySelectorAll<HTMLImageElement>("#urls img.image_thumbnail");
    for (const thumbnail of imageThumbnails) {
      if (thumbnail.complete && thumbnail.naturalWidth === 0) {
        thumbnail.src = `${searxng.settings.theme_static_path}/img/img_load_error.svg`;
      }

      thumbnail.onerror = () => {
        thumbnail.src = `${searxng.settings.theme_static_path}/img/img_load_error.svg`;
      };
    }

    const copyUrlButton = document.querySelector<HTMLButtonElement>("#search_url button#copy_url");
    copyUrlButton?.style.setProperty("display", "block");

    searxng.listen("click", ".btn-collapse", function (this: HTMLElement) {
      const btnLabelCollapsed = this.getAttribute("data-btn-text-collapsed");
      const btnLabelNotCollapsed = this.getAttribute("data-btn-text-not-collapsed");
      const target = this.getAttribute("data-target");

      if (!target || !btnLabelCollapsed || !btnLabelNotCollapsed) return;

      const targetElement = document.querySelector<HTMLElement>(target);
      assertElement(targetElement);

      const isCollapsed = this.classList.contains("collapsed");
      const newLabel = isCollapsed ? btnLabelNotCollapsed : btnLabelCollapsed;
      const oldLabel = isCollapsed ? btnLabelCollapsed : btnLabelNotCollapsed;

      this.innerHTML = this.innerHTML.replace(oldLabel, newLabel);
      this.classList.toggle("collapsed");

      targetElement.classList.toggle("invisible");
    });

    searxng.listen("click", ".media-loader", function (this: HTMLElement) {
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

    searxng.listen("click", "#copy_url", async function (this: HTMLElement) {
      const target = this.parentElement?.querySelector<HTMLPreElement>("pre");
      assertElement(target);

      await navigator.clipboard.writeText(target.innerText);
      const copiedText = this.dataset.copiedText;
      if (copiedText) {
        this.innerText = copiedText;
      }
    });

    searxng.selectImage = (resultElement: Element): void => {
      // add a class that can be evaluated in the CSS and indicates that the
      // detail view is open
      const resultsElement = document.getElementById("results");
      resultsElement?.classList.add("image-detail-open");

      // add a hash to the browser history so that pressing back doesn't return
      // to the previous page this allows us to dismiss the image details on
      // pressing the back button on mobile devices
      window.location.hash = "#image-viewer";

      searxng.scrollPageToSelected?.();

      // if there is no element given by the caller, stop here
      if (!resultElement) return;

      // find image element, if there is none, stop here
      const img = resultElement.querySelector<HTMLImageElement>(".result-images-source img");
      if (!img) return;

      // <img src="" data-src="http://example.org/image.jpg">
      const src = img.getAttribute("data-src");
      if (!src) return;

      // use thumbnail until full image loads
      const thumbnail = resultElement.querySelector<HTMLImageElement>(".image_thumbnail");
      if (thumbnail) {
        img.src = thumbnail.src;
      }

      // load full size image
      loadImage(src, () => {
        img.src = src;
        img.onerror = () => {
          img.src = `${searxng.settings.theme_static_path}/img/img_load_error.svg`;
        };

        img.removeAttribute("data-src");
      });
    };

    searxng.closeDetail = (): void => {
      const resultsElement = document.getElementById("results");
      resultsElement?.classList.remove("image-detail-open");

      // remove #image-viewer hash from url by navigating back
      if (window.location.hash === "#image-viewer") {
        window.history.back();
      }

      searxng.scrollPageToSelected?.();
    };

    searxng.listen("click", ".result-detail-close", (event: Event) => {
      event.preventDefault();
      searxng.closeDetail?.();
    });

    searxng.listen("click", ".result-detail-previous", (event: Event) => {
      event.preventDefault();
      searxng.selectPrevious?.(false);
    });

    searxng.listen("click", ".result-detail-next", (event: Event) => {
      event.preventDefault();
      searxng.selectNext?.(false);
    });

    // listen for the back button to be pressed and dismiss the image details when called
    window.addEventListener("hashchange", () => {
      if (window.location.hash !== "#image-viewer") {
        searxng.closeDetail?.();
      }
    });

    const swipeHorizontal = document.querySelectorAll<HTMLElement>(".swipe-horizontal");
    for (const element of swipeHorizontal) {
      searxng.listen("swiped-left", element, () => {
        searxng.selectNext?.(false);
      });

      searxng.listen("swiped-right", element, () => {
        searxng.selectPrevious?.(false);
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
  },
  { on: [searxng.endpoint === "results"] }
);
