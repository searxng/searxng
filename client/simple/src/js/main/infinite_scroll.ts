import { assertElement, searxng } from "./00_toolkit";

const newLoadSpinner = (): HTMLDivElement => {
  return Object.assign(document.createElement("div"), {
    className: "loader"
  });
};

const loadNextPage = async (onlyImages: boolean, callback: () => void): Promise<void> => {
  const searchForm = document.querySelector<HTMLFormElement>("#search");
  assertElement(searchForm);

  const form = document.querySelector<HTMLFormElement>("#pagination form.next_page");
  assertElement(form);

  const formData = new FormData(form);

  const action = searchForm.getAttribute("action");
  if (!action) {
    console.error("Form action not found");
    return;
  }

  const paginationElement = document.querySelector<HTMLElement>("#pagination");
  assertElement(paginationElement);

  paginationElement.replaceChildren(newLoadSpinner());

  try {
    const res = await searxng.http("POST", action, formData);
    const nextPage = await res.text();
    if (!nextPage) return;

    const nextPageDoc = new DOMParser().parseFromString(nextPage, "text/html");
    const articleList = nextPageDoc.querySelectorAll<HTMLElement>("#urls article");
    const nextPaginationElement = nextPageDoc.querySelector<HTMLElement>("#pagination");

    document.querySelector("#pagination")?.remove();

    const urlsElement = document.querySelector<HTMLElement>("#urls");
    if (!urlsElement) {
      console.error("URLs element not found");
      return;
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
      textContent: searxng.settings.translations?.error_loading_next_page ?? "Error loading next page",
      className: "dialog-error"
    });
    errorElement.setAttribute("role", "alert");
    document.querySelector("#pagination")?.replaceChildren(errorElement);
  }
};

searxng.ready(
  () => {
    const resultsElement = document.getElementById("results");
    if (!resultsElement) {
      console.error("Results element not found");
      return;
    }

    const onlyImages = resultsElement.classList.contains("only_template_images");
    const observedSelector = "article.result:last-child";

    const intersectionObserveOptions: IntersectionObserverInit = {
      rootMargin: "320px"
    };

    const observer = new IntersectionObserver(async (entries: IntersectionObserverEntry[]) => {
      const [paginationEntry] = entries;

      if (paginationEntry?.isIntersecting) {
        observer.unobserve(paginationEntry.target);

        await loadNextPage(onlyImages, () => {
          const nextObservedElement = document.querySelector<HTMLElement>(observedSelector);
          if (nextObservedElement) {
            observer.observe(nextObservedElement);
          }
        });
      }
    }, intersectionObserveOptions);

    const initialObservedElement = document.querySelector<HTMLElement>(observedSelector);
    if (initialObservedElement) {
      observer.observe(initialObservedElement);
    }
  },
  {
    on: [searxng.endpoint === "results", searxng.settings.infinite_scroll]
  }
);
