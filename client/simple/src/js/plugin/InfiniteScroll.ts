// SPDX-License-Identifier: AGPL-3.0-or-later

import { Plugin } from "../Plugin.ts";
import { http, settings } from "../toolkit.ts";
import { assertElement } from "../util/assertElement.ts";
import { getElement } from "../util/getElement.ts";

/**
 * Automatically loads the next page when scrolling to bottom of the current page.
 */
export default class InfiniteScroll extends Plugin {
  public constructor() {
    super("infiniteScroll");
  }

  protected async run(): Promise<void> {
    const resultsElement = getElement<HTMLElement>("results");

    const onlyImages: boolean = resultsElement.classList.contains("only_template_images");
    const observedSelector = "article.result:last-child";

    const spinnerElement = document.createElement("div");
    spinnerElement.className = "loader";

    const loadNextPage = async (callback: () => void): Promise<void> => {
      const searchForm = document.querySelector<HTMLFormElement>("#search");
      assertElement(searchForm);

      const form = document.querySelector<HTMLFormElement>("#pagination form.next_page");
      assertElement(form);

      const action = searchForm.getAttribute("action");
      if (!action) {
        throw new Error("Form action not defined");
      }

      const paginationElement = document.querySelector<HTMLElement>("#pagination");
      assertElement(paginationElement);

      paginationElement.replaceChildren(spinnerElement);

      try {
        const res = await http("POST", action, { body: new FormData(form) });
        const nextPage = await res.text();
        if (!nextPage) return;

        const nextPageDoc = new DOMParser().parseFromString(nextPage, "text/html");
        const articleList = nextPageDoc.querySelectorAll<HTMLElement>("#urls article");
        const nextPaginationElement = nextPageDoc.querySelector<HTMLElement>("#pagination");

        document.querySelector("#pagination")?.remove();

        const urlsElement = document.querySelector<HTMLElement>("#urls");
        if (!urlsElement) {
          throw new Error("URLs element not found");
        }

        if (articleList.length > 0 && !onlyImages) {
          // do not add <hr> element when there are only images
          urlsElement.appendChild(document.createElement("hr"));
        }

        urlsElement.append(...Array.from(articleList));

        if (nextPaginationElement) {
          const results = document.querySelector<HTMLElement>("#results");
          results?.appendChild(nextPaginationElement);
          callback();
        }
      } catch (error) {
        console.error("Error loading next page:", error);

        const errorElement = Object.assign(document.createElement("div"), {
          textContent: settings.translations?.error_loading_next_page ?? "Error loading next page",
          className: "dialog-error"
        });
        errorElement.setAttribute("role", "alert");
        document.querySelector("#pagination")?.replaceChildren(errorElement);
      }
    };

    const intersectionObserveOptions: IntersectionObserverInit = {
      rootMargin: "320px"
    };

    const observer: IntersectionObserver = new IntersectionObserver((entries: IntersectionObserverEntry[]) => {
      const [paginationEntry] = entries;

      if (paginationEntry?.isIntersecting) {
        observer.unobserve(paginationEntry.target);

        void loadNextPage(() => {
          const nextObservedElement = document.querySelector<HTMLElement>(observedSelector);
          if (nextObservedElement) {
            observer.observe(nextObservedElement);
          }
        }).then(() => {
          // wait until promise is resolved
        });
      }
    }, intersectionObserveOptions);

    const initialObservedElement: HTMLElement | null = document.querySelector<HTMLElement>(observedSelector);
    if (initialObservedElement) {
      observer.observe(initialObservedElement);
    }
  }

  protected async post(): Promise<void> {
    // noop
  }
}
