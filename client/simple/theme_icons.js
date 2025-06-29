/**
 * Generate icons.html for the jinja templates of the simple theme.
 */

import { dirname, resolve } from "node:path";
import { argv } from "node:process";
import { jinja_svg_sets } from "./tools/jinja_svg_catalog.js";

const HERE = `${dirname(argv[1])}/`;
const dest = resolve(HERE, "../../searx/templates/simple/icons.html");

/** @type import("./tools/jinja_svg_catalog.js").JinjaMacro[] */
const searxng_jinja_macros = [
  { name: "icon", class: "sxng-icon-set" },
  { name: "icon_small", class: "sxng-icon-set-small" },
  { name: "icon_big", class: "sxng-icon-set-big" }
];

const sxng_icon_opts = {
  multipass: true,
  plugins: [
    { name: "removeTitle" },
    { name: "removeXMLNS" },
    {
      name: "addAttributesToSVGElement",
      params: {
        attributes: [
          {
            "aria-hidden": "true"
          }
        ]
      }
    }
  ]
};

/**
 * @type import("./tools/jinja_svg_catalog.js").IconSet[]
 */
const simple_icons = [
  {
    base: resolve(HERE, "node_modules/ionicons/dist/svg"),
    set: {
      alert: "alert-outline.svg",
      appstore: "apps-outline.svg",
      book: "book-outline.svg",
      close: "close-outline.svg",
      download: "download-outline.svg",
      "ellipsis-vertical": "ellipsis-vertical-outline.svg",
      "file-tray-full": "file-tray-full-outline.svg",
      film: "film-outline.svg",
      globe: "globe-outline.svg",
      heart: "heart-outline.svg",
      image: "image-outline.svg",
      layers: "layers-outline.svg",
      leecher: "arrow-down.svg",
      location: "location-outline.svg",
      magnet: "magnet-outline.svg",
      "musical-notes": "musical-notes-outline.svg",
      "navigate-down": "chevron-down-outline.svg",
      "navigate-left": "chevron-back-outline.svg",
      "navigate-right": "chevron-forward-outline.svg",
      "navigate-up": "chevron-up-outline.svg",
      people: "people-outline.svg",
      play: "play-outline.svg",
      radio: "radio-outline.svg",
      save: "save-outline.svg",
      school: "school-outline.svg",
      search: "search-outline.svg",
      seeder: "swap-vertical.svg",
      settings: "settings-outline.svg",
      tv: "tv-outline.svg"
    },
    svgo_opts: sxng_icon_opts
  },
  // some of the ionicons are not suitable for a dark theme, we fixed the svg
  // manually in src/svg/ionicons
  // - https://github.com/searxng/searxng/pull/4284#issuecomment-2680550342
  {
    base: resolve(HERE, "src/svg/ionicons"),
    set: {
      "information-circle": "information-circle-outline.svg",
      newspaper: "newspaper-outline.svg"
    },
    svgo_opts: sxng_icon_opts
  }
];

jinja_svg_sets(dest, searxng_jinja_macros, simple_icons);
