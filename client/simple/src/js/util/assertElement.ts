// SPDX-License-Identifier: AGPL-3.0-or-later

type AssertElement = <T>(element?: T | null) => asserts element is T;
export const assertElement: AssertElement = <T>(element?: T | null): asserts element is T => {
  if (!element) {
    throw new Error("DOM element not found");
  }
};
