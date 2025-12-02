// SPDX-License-Identifier: AGPL-3.0-or-later

import { http, listen, settings } from "../toolkit.ts";
import { assertElement } from "../util/assertElement.ts";

const fetchResults = async (qInput: HTMLInputElement, query: string): Promise<void> => {
  try {
    let res: Response;

    if (settings.method === "GET") {
      res = await http("GET", `./autocompleter?q=${query}`);
    } else {
      res = await http("POST", "./autocompleter", { body: new URLSearchParams({ q: query }) });
    }

    const results = await res.json();

    const autocomplete = document.querySelector<HTMLElement>(".autocomplete");
    assertElement(autocomplete);

    const autocompleteList = document.querySelector<HTMLUListElement>(".autocomplete ul");
    assertElement(autocompleteList);

    autocomplete.classList.add("open");
    autocompleteList.replaceChildren();

    // show an error message that no result was found
    if (results?.[1]?.length === 0) {
      const noItemFoundMessage = Object.assign(document.createElement("li"), {
        className: "no-item-found",
        textContent: settings.translations?.no_item_found ?? "No results found"
      });
      autocompleteList.append(noItemFoundMessage);
      return;
    }

    const fragment = new DocumentFragment();

    for (const result of results[1]) {
      const li = Object.assign(document.createElement("li"), { textContent: result });

      listen("mousedown", li, () => {
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

const qInput = document.getElementById("q") as HTMLInputElement | null;
assertElement(qInput);

let timeoutId: number;

listen("input", qInput, () => {
  clearTimeout(timeoutId);

  const query = qInput.value;
  const minLength = settings.autocomplete_min ?? 2;

  if (query.length < minLength) return;

  timeoutId = window.setTimeout(async () => {
    if (query === qInput.value) {
      await fetchResults(qInput, query);
    }
  }, 300);
});

const autocomplete: HTMLElement | null = document.querySelector<HTMLElement>(".autocomplete");
const autocompleteList: HTMLUListElement | null = document.querySelector<HTMLUListElement>(".autocomplete ul");
if (autocompleteList) {
  listen("keyup", qInput, (event: KeyboardEvent) => {
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
      default:
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
