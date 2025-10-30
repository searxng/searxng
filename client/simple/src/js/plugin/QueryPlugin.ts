// SPDX-License-Identifier: AGPL-3.0-or-later

import { Plugin } from "../core/Plugin.ts";
import { getElement } from "../core/util/getElement.ts";

export default class QueryPlugin extends Plugin {
  public readonly name = "query";

  protected async do(): Promise<HTMLSpanElement> {
    const searchInput = getElement<HTMLInputElement>("q");
    const searchQuery = searchInput.value.trim();

    const response = document.createElement("span");
    response.textContent = `Query: ${searchQuery}`;

    return response;
  }
}
