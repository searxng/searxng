// SPDX-License-Identifier: AGPL-3.0-or-later

import { getElement } from "./util/getElement.ts";

export abstract class Plugin {
  protected abstract readonly name: string;

  public constructor() {
    void this.invoke();
  }

  private async invoke(): Promise<void> {
    try {
      const response = await this.do();

      console.debug(`[PLUGIN] ${this.name}: OK`);

      if (!response) return;
      if (response instanceof HTMLElement || typeof response === "string" || typeof response === "number") {
        await this.insertAnswerContainer(response);
      }
    } catch (error) {
      console.error(`[PLUGIN] ${this.name}:`, error);
    }
  }

  protected abstract do(): Promise<unknown> | unknown;

  private async insertAnswerContainer(element: HTMLElement | string | number): Promise<void> {
    const results = getElement<HTMLDivElement>("results");

    // ./searx/templates/elements/answers.html
    let answers = getElement<HTMLDivElement>("answers", { assert: false });
    if (!answers) {
      // what is this?
      const answersTitle = document.createElement("h4");
      answersTitle.setAttribute("class", "title");
      answersTitle.setAttribute("id", "answers-title");
      answersTitle.textContent = "Answers : ";

      answers = document.createElement("div");
      answers.setAttribute("id", "answers");
      answers.setAttribute("role", "complementary");
      answers.setAttribute("aria-labelledby", "answers-title");
      answers.appendChild(answersTitle);
    }

    if (!(element instanceof HTMLElement)) {
      const span = document.createElement("span");
      span.innerHTML = element.toString();
      // biome-ignore lint/style/noParameterAssign: TODO
      element = span;
    }

    answers.appendChild(element);

    results.insertAdjacentElement("afterbegin", answers);
  }
}
