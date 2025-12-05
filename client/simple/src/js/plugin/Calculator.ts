// SPDX-License-Identifier: AGPL-3.0-or-later

import {
  absDependencies,
  addDependencies,
  create,
  createUnitDependencies,
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
  subtractDependencies,
  toDependencies,
  unitDependencies
} from "mathjs";
import { Plugin } from "../Plugin.ts";
import { appendAnswerElement } from "../util/appendAnswerElement.ts";
import { getElement } from "../util/getElement.ts";

/**
 * Parses and solves expressions. Can evaluate functions, do arithmetic and
 * handle units.
 *
 * @example
 * "(gcd(48, 18) + 3.33) / pi" = "2.969831238094767"
 * "2 hours - 3600 seconds" = "1 hours"
 * "5 feet to cm" = "152.4 cm"
 *
 * @remarks
 * Depends on `mathjs` library.
 *
 * https://mathjs.org/docs/datatypes/units.html#reference
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
    ...createUnitDependencies,
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
    ...subtractDependencies,
    ...toDependencies,
    ...unitDependencies
  });

  protected async run(): Promise<string | undefined> {
    Calculator.math.createUnit({
      mph: "1 mile/hour",
      knot: {
        definition: "0.514444444 m/s",
        aliases: ["knots", "kt", "kts"]
      }
    });

    const searchInput = getElement<HTMLInputElement>("q");
    const searchInputValueNormalized = searchInput.value.replaceAll("º", "deg");
    const node = Calculator.math.parse(searchInputValueNormalized);

    try {
      return `${node.toString()} = ${node.evaluate()}`;
    } catch (why) {
      // not a compatible expression
      console.debug(why);
      return;
    }
  }

  protected async post(result: string): Promise<void> {
    appendAnswerElement(result);
  }
}
