/**
 * CONFIG: https://vite.dev/config/
 */

import { resolve } from "node:path";
import browserslistToEsbuild from "browserslist-to-esbuild";
import { browserslistToTargets } from "lightningcss";
import type { Config } from "svgo";
import type { UserConfig } from "vite";
import { browserslist } from "./package.json";
import { plg_svg2png, plg_svg2svg } from "./tools/plg";

const ROOT = "../../"; // root of the git repository

const PATH = {
  brand: "src/brand/",
  dist: resolve(ROOT, "searx/static/themes/simple/"),
  modules: "node_modules/",
  src: "src/",
  templates: resolve(ROOT, "searx/templates/simple/")
};

const svg2svg_opts: Config = {
  plugins: [{ name: "preset-default" }, "sortAttrs", "convertStyleToAttrs"]
};

const svg2svg_favicon_opts: Config = {
  plugins: [{ name: "preset-default" }, "sortAttrs"]
};

export default {
  base: "/static/themes/simple/",
  publicDir: "static/",
  mode: "production",
  // mode: "development",

  build: {
    target: browserslistToEsbuild(browserslist),
    cssTarget: browserslistToEsbuild(browserslist),
    manifest: "manifest.json",
    emptyOutDir: true,
    assetsDir: "",
    outDir: PATH.dist,

    sourcemap: true,

    rollupOptions: {
      input: {
        // build CSS files
        "searxng-ltr.min.css": `${PATH.src}/less/style-ltr.less`,
        "searxng-rtl.min.css": `${PATH.src}/less/style-rtl.less`,
        "rss.min.css": `${PATH.src}/less/rss.less`,

        // build script files
        "searxng.min": `${PATH.src}/js/main/index.ts`,

        // ol
        "ol.min": `${PATH.src}/js/pkg/ol.ts`,
        "ol.min.css": `${PATH.modules}/ol/ol.css`
      },

      // file naming conventions / pathnames are relative to outDir (PATH.dist)
      output: {
        entryFileNames: "js/[name].js",
        chunkFileNames: "js/[name].js",
        assetFileNames: ({ names }) => {
          const [name] = names;

          const extension = name?.split(".").pop();
          switch (extension) {
            case "css":
              return `css/[name][extname]`;
            case "js":
              return `js/[name][extname]`;
            case "png":
            case "svg":
              return `img/[name][extname]`;
            default:
              console.warn("Unknown asset:", name);
              return `[name][extname]`;
          }
        }
      }
    }
  }, // end: build

  plugins: [
    // -- svg images
    plg_svg2svg(
      [
        { src: `${PATH.src}/svg/empty_favicon.svg`, dest: `${PATH.dist}/img/empty_favicon.svg` },
        { src: `${PATH.src}/svg/select-dark.svg`, dest: `${PATH.dist}/img/select-dark.svg` },
        { src: `${PATH.src}/svg/select-light.svg`, dest: `${PATH.dist}/img/select-light.svg` }
      ],
      svg2svg_opts
    ),

    // SearXNG brand (static)
    plg_svg2png([
      { src: `${PATH.brand}/searxng-wordmark.svg`, dest: `${PATH.dist}/img/favicon.png` },
      { src: `${PATH.brand}/searxng.svg`, dest: `${PATH.dist}/img/searxng.png` }
    ]),

    // -- svg
    plg_svg2svg(
      [
        { src: `${PATH.brand}/searxng.svg`, dest: `${PATH.dist}/img/searxng.svg` },
        { src: `${PATH.brand}/img_load_error.svg`, dest: `${PATH.dist}/img/img_load_error.svg` }
      ],
      svg2svg_opts
    ),

    // -- favicon
    plg_svg2svg(
      [{ src: `${PATH.brand}/searxng-wordmark.svg`, dest: `${PATH.dist}/img/favicon.svg` }],
      svg2svg_favicon_opts
    ),

    // -- simple templates
    plg_svg2svg(
      [{ src: `${PATH.brand}/searxng-wordmark.svg`, dest: `${PATH.templates}/searxng-wordmark.min.svg` }],
      svg2svg_opts
    )
  ], // end: plugins

  // FIXME: missing CCS sourcemaps!!
  // see: https://github.com/vitejs/vite/discussions/13845#discussioncomment-11992084
  //
  // what I have tried so far (see config below):
  //
  // - build.sourcemap
  // - esbuild.sourcemap
  // - css.preprocessorOptions.less.sourceMap
  css: {
    transformer: "lightningcss",
    lightningcss: {
      targets: browserslistToTargets(browserslist)
    },
    devSourcemap: true
  }, // end: css

  experimental: {
    enableNativePlugin: true
  } // end: experimental
} satisfies UserConfig;
