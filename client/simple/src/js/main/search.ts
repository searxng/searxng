import { assertElement, searxng } from "./00_toolkit.ts";

const submitIfQuery = (qInput: HTMLInputElement): void => {
  if (qInput.value.length > 0) {
    const search = document.getElementById("search") as HTMLFormElement | null;
    search?.submit();
  }
};

const updateClearButton = (qInput: HTMLInputElement, cs: HTMLElement): void => {
  cs.classList.toggle("empty", qInput.value.length === 0);
};

const createClearButton = (qInput: HTMLInputElement): void => {
  const cs = document.getElementById("clear_search");
  assertElement(cs);

  updateClearButton(qInput, cs);

  searxng.listen("click", cs, (event: MouseEvent) => {
    event.preventDefault();
    qInput.value = "";
    qInput.focus();
    updateClearButton(qInput, cs);
  });

  searxng.listen("input", qInput, () => updateClearButton(qInput, cs), { passive: true });
};

const fetchResults = async (qInput: HTMLInputElement, query: string): Promise<void> => {
  try {
    let res: Response;

    if (searxng.settings.method === "GET") {
      res = await searxng.http("GET", `./autocompleter?q=${query}`);
    } else {
      res = await searxng.http("POST", "./autocompleter", new URLSearchParams({ q: query }));
    }

    const results = await res.json();

    const autocomplete = document.querySelector<HTMLElement>(".autocomplete");
    assertElement(autocomplete);

    const autocompleteList = document.querySelector<HTMLUListElement>(".autocomplete ul");
    assertElement(autocompleteList);

    autocomplete.classList.add("open");
    autocompleteList.replaceChildren();

    // show an error message that no result was found
    if (!results?.[1]?.length) {
      const noItemFoundMessage = Object.assign(document.createElement("li"), {
        className: "no-item-found",
        textContent: searxng.settings.translations?.no_item_found ?? "No results found"
      });
      autocompleteList.append(noItemFoundMessage);
      return;
    }

    const fragment = new DocumentFragment();

    for (const result of results[1]) {
      const li = Object.assign(document.createElement("li"), { textContent: result });

      searxng.listen("mousedown", li, () => {
        qInput.value = result;

        const form = document.querySelector<HTMLFormElement>("#search");
        form?.submit();

        autocomplete.classList.remove("open");
      });

      fragment.append(li);
    }

    autocompleteList.append(fragment);
  } catch (error) {
    console.error("Error fetching autocomplete results:", error);
  }
};

searxng.ready(
  () => {
    const qInput = document.getElementById("q") as HTMLInputElement | null;
    assertElement(qInput);

    const isMobile = window.matchMedia("(max-width: 50em)").matches;
    const isResultsPage = document.querySelector("main")?.id === "main_results";

    // focus search input on large screens
    if (!isMobile && !isResultsPage) {
      qInput.focus();
    }

    createClearButton(qInput);

    // autocompleter
    if (searxng.settings.autocomplete) {
      let timeoutId: number;

      searxng.listen("input", qInput, () => {
        clearTimeout(timeoutId);

        const query = qInput.value;
        const minLength = searxng.settings.autocomplete_min ?? 2;

        if (query.length < minLength) return;

        timeoutId = window.setTimeout(async () => {
          if (query === qInput.value) {
            await fetchResults(qInput, query);
          }
        }, 300);
      });

      const autocomplete = document.querySelector<HTMLElement>(".autocomplete");
      const autocompleteList = document.querySelector<HTMLUListElement>(".autocomplete ul");
      if (autocompleteList) {
        searxng.listen("keyup", qInput, (event: KeyboardEvent) => {
          const listItems = [...autocompleteList.children] as HTMLElement[];

          const currentIndex = listItems.findIndex((item) => item.classList.contains("active"));
          let newCurrentIndex = -1;

          switch (event.key) {
            case "ArrowUp": {
              const currentItem = listItems[currentIndex];
              if (currentItem && currentIndex >= 0) {
                currentItem.classList.remove("active");
              }
              // we need to add listItems.length to the index calculation here because the JavaScript modulos
              // operator doesn't work with negative numbers
              newCurrentIndex = (currentIndex - 1 + listItems.length) % listItems.length;
              break;
            }
            case "ArrowDown": {
              const currentItem = listItems[currentIndex];
              if (currentItem && currentIndex >= 0) {
                currentItem.classList.remove("active");
              }
              newCurrentIndex = (currentIndex + 1) % listItems.length;
              break;
            }
            case "Tab":
            case "Enter":
              if (autocomplete) {
                autocomplete.classList.remove("open");
              }
              break;
          }

          if (newCurrentIndex !== -1) {
            const selectedItem = listItems[newCurrentIndex];
            if (selectedItem) {
              selectedItem.classList.add("active");

              if (!selectedItem.classList.contains("no-item-found")) {
                const qInput = document.getElementById("q") as HTMLInputElement | null;
                if (qInput) {
                  qInput.value = selectedItem.textContent ?? "";
                }
              }
            }
          }
        });
      }
    }

    // Additionally to searching when selecting a new category, we also
    // automatically start a new search request when the user changes a search
    // filter (safesearch, time range or language) (this requires JavaScript
    // though)
    if (
      searxng.settings.search_on_category_select &&
      // If .search_filters is undefined (invisible) we are on the homepage and
      // hence don't have to set any listeners
      document.querySelector(".search_filters")
    ) {
      const safesearchElement = document.getElementById("safesearch");
      if (safesearchElement) {
        searxng.listen("change", safesearchElement, () => submitIfQuery(qInput));
      }

      const timeRangeElement = document.getElementById("time_range");
      if (timeRangeElement) {
        searxng.listen("change", timeRangeElement, () => submitIfQuery(qInput));
      }

      const languageElement = document.getElementById("language");
      if (languageElement) {
        searxng.listen("change", languageElement, () => submitIfQuery(qInput));
      }
    }

    const categoryButtons = [...document.querySelectorAll<HTMLButtonElement>("button.category_button")];
    for (const button of categoryButtons) {
      searxng.listen("click", button, (event: MouseEvent) => {
        if (event.shiftKey) {
          event.preventDefault();
          button.classList.toggle("selected");
          return;
        }

        // deselect all other categories
        for (const categoryButton of categoryButtons) {
          categoryButton.classList.toggle("selected", categoryButton === button);
        }
      });
    }

    const form = document.querySelector<HTMLFormElement>("#search");
    assertElement(form);

    // override form submit action to update the actually selected categories
    searxng.listen("submit", form, (event: Event) => {
      event.preventDefault();

      const categoryValuesInput = document.querySelector<HTMLInputElement>("#selected-categories");
      if (categoryValuesInput) {
        const categoryValues = categoryButtons
          .filter((button) => button.classList.contains("selected"))
          .map((button) => button.name.replace("category_", ""));

        categoryValuesInput.value = categoryValues.join(",");
      }

      form.submit();
    });
  },
  { on: [searxng.endpoint === "index" || searxng.endpoint === "results"] }
);
