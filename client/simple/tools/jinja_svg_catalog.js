import fs from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Edge } from "edge.js";
import { optimize as svgo } from "svgo";

const __dirname = dirname(fileURLToPath(import.meta.url));
const __jinja_class_placeholder__ = "__jinja_class_placeholder__";

// -- types

/**
 * @typedef {object} IconSet - A set of icons
 * @property {object} set - Object of SVG icons, where property name is the
 * name of the icon and value is the src of the SVG (relative to base).
 * @property {string} base - Folder in which the SVG src files are located.
 * @property {import("svgo").Config} svgo_opts - svgo options for this set.
 */

/**
 * @typedef {object} IconSVG - Mapping of icon name to SVG source file.
 * @property {string} name - Name of the icon isource file.
 * @property {string} src - Name of the destination file.
 * @property {import("svgo").Config} svgo_opts - Options passed to svgo.
 */

/**
 * @typedef {object} JinjaMacro - Arguments to create a jinja macro
 * @property {string} name - Name of the jinja macro.
 * @property {string} class - SVG's class name (value of XML class attribute)
 */

// -- functions

/**
 * Generate a jinja template with a catalog of SVG icons that can be
 * used in in other HTML jinja templates.
 *
 * @param {string} dest - filename of the generate jinja template.
 * @param {JinjaMacro} macros - Jinja macros to create.
 * @param {IconSVG[]} items - Array of SVG items.
 */

function jinja_svg_catalog(dest, macros, items) {
  const svg_catalog = {};
  const edge_template = resolve(__dirname, "jinja_svg_catalog.html.edge");

  items.forEach((item) => {
    /** @type {import("svgo").Config} */
    // JSON.stringify & JSON.parse are used to create a deep copy of the
    // item.svgo_opts object
    const svgo_opts = JSON.parse(JSON.stringify(item.svgo_opts));
    svgo_opts.plugins.push({
      name: "addClassesToSVGElement",
      params: {
        classNames: [__jinja_class_placeholder__]
      }
    });

    try {
      const raw = fs.readFileSync(item.src, "utf8");
      const opt = svgo(raw, svgo_opts);
      svg_catalog[item.name] = opt.data;
    } catch (err) {
      console.error(`ERROR: jinja_svg_catalog processing ${item.name} src: ${item.src} -- ${err}`);
      throw err;
    }
  });

  fs.mkdir(dirname(dest), { recursive: true }, (err) => {
    if (err) throw err;
  });

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
}

/**
 * Calls jinja_svg_catalog for a collection of icon sets where each set has its
 * own parameters.
 *
 * @param {string} dest - filename of the generate jinja template.
 * @param {JinjaMacro} macros - Jinja macros to create.
 * @param {IconSet[]} sets - Array of SVG sets.
 */
function jinja_svg_sets(dest, macros, sets) {
  /** @type IconSVG[] */
  const items = [];
  const all = [];
  for (const obj of sets) {
    for (const [name, file] of Object.entries(obj.set)) {
      if (all.includes(name)) {
        throw new Error(`ERROR: ${name} has already been defined`);
      }
      items.push({
        name: name,
        src: resolve(obj.base, file),
        svgo_opts: obj.svgo_opts
      });
    }
    jinja_svg_catalog(dest, macros, items);
  }
}

// -- exports

export { jinja_svg_sets, jinja_svg_catalog };
