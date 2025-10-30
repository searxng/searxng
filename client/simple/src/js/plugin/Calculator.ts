// SPDX-License-Identifier: AGPL-3.0-or-later

import {
  absDependencies,
  addDependencies,
  create,
  divideDependencies,
  eDependencies,
  evaluateDependencies,
  expDependencies,
  factorialDependencies,
  gcdDependencies,
  lcmDependencies,
  log1pDependencies,
  log2Dependencies,
  log10Dependencies,
  logDependencies,
  modDependencies,
  multiplyDependencies,
  nthRootDependencies,
  piDependencies,
  powDependencies,
  roundDependencies,
  signDependencies,
  sqrtDependencies,
  subtractDependencies
} from "mathjs/number";
import { Plugin } from "../Plugin.ts";
import { appendAnswerElement } from "../util/appendAnswerElement.ts";
import { getElement } from "../util/getElement.ts";

/**
 * Parses and solves mathematical expressions. Can do basic arithmetic and
 * evaluate some functions.
 *
 * @example
 * "(3 + 5) / 2" = "4"
 * "e ^ 2 + pi" = "10.530648752520442"
 * "gcd(48, 18) + lcm(4, 5)" = "26"
 *
 * @remarks
 * Depends on `mathjs` library.
 */
export default class Calculator extends Plugin {
  public constructor() {
    super("calculator");
  }

  /**
   * @remarks
   * Compare bundle size after adding or removing features.
   */
  private static readonly math = create({
    ...absDependencies,
    ...addDependencies,
    ...divideDependencies,
    ...eDependencies,
    ...evaluateDependencies,
    ...expDependencies,
    ...factorialDependencies,
    ...gcdDependencies,
    ...lcmDependencies,
    ...log10Dependencies,
    ...log1pDependencies,
    ...log2Dependencies,
    ...logDependencies,
    ...modDependencies,
    ...multiplyDependencies,
    ...nthRootDependencies,
    ...piDependencies,
    ...powDependencies,
    ...roundDependencies,
    ...signDependencies,
    ...sqrtDependencies,
    ...subtractDependencies
  });

  protected async run(): Promise<string | undefined> {
    const searchInput = getElement<HTMLInputElement>("q");
    const node = Calculator.math.parse(searchInput.value);

    try {
      return `${node.toString()} = ${node.evaluate()}`;
    } catch {
      // not a compatible math expression
      return;
    }
  }

  protected async post(result: string): Promise<void> {
    appendAnswerElement(result);
  }
}
