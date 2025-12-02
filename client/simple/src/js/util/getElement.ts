// SPDX-License-Identifier: AGPL-3.0-or-later

import { assertElement } from "./assertElement.ts";

type Options = {
  assert?: boolean;
};

export function getElement<T>(id: string, options?: { assert: true }): T;
export function getElement<T>(id: string, options?: { assert: false }): T | null;
export function getElement<T>(id: string, options: Options = {}): T | null {
  options.assert ??= true;

  const element = document.getElementById(id) as T | null;

  if (options.assert) {
    assertElement(element);
  }

  return element;
}
