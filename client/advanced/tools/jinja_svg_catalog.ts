// SPDX-License-Identifier: AGPL-3.0-or-later

import fs from "node:fs";
import { dirname, resolve } from "node:path";
import { Edge } from "edge.js";
import { type Config as SvgoConfig, optimize as svgo } from "svgo";

const __jinja_class_placeholder__ = "__jinja_class_placeholder__";

// A set of icons
export type IconSet = {
  // Object of SVG icons, where property name is the name of the icon and value is the src of the SVG (relative to base)
  set: Record<string, string>;
  // Folder in which the SVG src files are located
  base: string;
  // svgo options for this set
  svgo_opts: SvgoConfig;
};

// Mapping of icon name to SVG source file
type IconSVG = {
  // Name of the icon isource file
  name: string;
  // Name of the destination file
  src: string;
  // Options passed to svgo
  svgo_opts: SvgoConfig;
};

// Arguments to create a jinja macro
export type JinjaMacro = {
  // Name of the jinja macro
  name: string;
  // SVG's class name (value of XML class attribute)
  class: string;
};

/**
 * Generate a jinja template with a catalog of SVG icons that can be
 * used in other HTML jinja templates.
 *
 * @param dest - filename of the generate jinja template.
 * @param macros - Jinja macros to create.
 * @param items - Array of SVG items.
 */
export const jinja_svg_catalog = (dest: string, macros: JinjaMacro[], items: IconSVG[]): void => {
  const svg_catalog: Record<string, string> = {};
  const edge_template = resolve(import.meta.dirname, "jinja_svg_catalog.html.edge");

  for (const item of items) {
    // JSON.stringify & JSON.parse are used to create a deep copy of the item.svgo_opts object
    const svgo_opts: SvgoConfig = JSON.parse(JSON.stringify(item.svgo_opts));

    svgo_opts.plugins?.push({
      name: "addClassesToSVGElement",
      params: {
        classNames: [__jinja_class_placeholder__]
      }
    });

    try {
      const raw = fs.readFileSync(item.src, "utf8");
      const opt = svgo(raw, svgo_opts);

      svg_catalog[item.name] = opt.data;
    } catch (error) {
      console.error(`ERROR: jinja_svg_catalog processing ${item.name} src: ${item.src} -- ${error}`);
      throw error;
    }
  }

  fs.mkdirSync(dirname(dest), { recursive: true });

  const ctx = {
    svg_catalog: svg_catalog,
    macros: macros,
    edge_template: edge_template,
    __jinja_class_placeholder__: __jinja_class_placeholder__,
    // see https://github.com/edge-js/edge/issues/162
    open_curly_brace: "{{",
    close_curly_brace: "}}"
  };

  const jinjatmpl = Edge.create().renderRawSync(fs.readFileSync(edge_template, "utf-8"), ctx);

  fs.writeFileSync(dest, jinjatmpl);
  console.log(`[jinja_svg_catalog] created: ${dest}`);
};

/**
 * Calls jinja_svg_catalog for a collection of icon sets where each set has its
 * own parameters.
 *
 * @param dest - filename of the generate jinja template.
 * @param macros - Jinja macros to create.
 * @param sets - Array of SVG sets.
 */
export const jinja_svg_sets = (dest: string, macros: JinjaMacro[], sets: IconSet[]): void => {
  const items: IconSVG[] = [];
  const all: string[] = [];

  for (const obj of sets) {
    for (const [name, file] of Object.entries(obj.set)) {
      if (all.includes(name)) {
        throw new Error(`ERROR: ${name} has already been defined`);
      }

      all.push(name);
      items.push({
        name: name,
        src: resolve(obj.base, file),
        svgo_opts: obj.svgo_opts
      });
    }
  }

  jinja_svg_catalog(dest, macros, items);
};
