// SPDX-License-Identifier: AGPL-3.0-or-later

import { getElement } from "./getElement.ts";

export const appendAnswerElement = (element: HTMLElement | string | number): void => {
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
};
