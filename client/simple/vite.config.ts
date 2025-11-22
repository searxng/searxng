// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * CONFIG: https://vite.dev/config/
 */

import { resolve } from "node:path";
import { constants as zlibConstants } from "node:zlib";
import browserslistToEsbuild from "browserslist-to-esbuild";
import { browserslistToTargets } from "lightningcss";
import type { PreRenderedAsset } from "rolldown";
import type { Config } from "svgo";
import type { UserConfig } from "vite";
import analyzer from "vite-bundle-analyzer";
import manifest from "./package.json" with { type: "json" };
import { plg_svg2png, plg_svg2svg } from "./tools/plg.ts";

const ROOT = "../../"; // root of the git repository

const PATH = {
  brand: "src/brand/",
  dist: resolve(ROOT, "searx/static/themes/simple/"),
  modules: "node_modules/",
  src: "src/",
  templates: resolve(ROOT, "searx/templates/simple/")
} as const;

const svg2svg_opts: Config = {
  plugins: [{ name: "preset-default" }, "sortAttrs", "convertStyleToAttrs"]
};

const svg2svg_favicon_opts: Config = {
  plugins: [{ name: "preset-default" }, "sortAttrs"]
};

export default {
  base: "/static/themes/simple/",
  publicDir: "static/",

  build: {
    target: browserslistToEsbuild(manifest.browserslist),
    assetsDir: "",
    outDir: PATH.dist,
    manifest: "manifest.json",
    emptyOutDir: true,
    sourcemap: true,
    rolldownOptions: {
      input: {
        // entrypoint
        core: `${PATH.src}/js/index.ts`,

        // stylesheets
        ltr: `${PATH.src}/less/style-ltr.less`,
        rtl: `${PATH.src}/less/style-rtl.less`,
        rss: `${PATH.src}/less/rss.less`
      },

      // file naming conventions / pathnames are relative to outDir (PATH.dist)
      output: {
        entryFileNames: "sxng-[name].min.js",
        chunkFileNames: "chunk/[hash].min.js",
        assetFileNames: ({ names }: PreRenderedAsset): string => {
          const [name] = names;

          switch (name?.split(".").pop()) {
            case "css":
              return "sxng-[name].min[extname]";
            default:
              return "sxng-[name][extname]";
          }
        },
        sanitizeFileName: (name: string): string => {
          return name
            .normalize("NFD")
            .replace(/[^a-zA-Z0-9.-]/g, "_")
            .toLowerCase();
        }
      }
    }
  }, // end: build

  plugins: [
    // -- bundle analyzer
    analyzer({
      enabled: process.env.VITE_BUNDLE_ANALYZE === "true",
      analyzerPort: "auto",
      summary: true,
      reportTitle: manifest.name,

      // sidecars with max compression
      gzipOptions: {
        level: zlibConstants.Z_BEST_COMPRESSION
      },
      brotliOptions: {
        params: {
          [zlibConstants.BROTLI_PARAM_QUALITY]: zlibConstants.BROTLI_MAX_QUALITY
        }
      }
    }),

    // -- svg images
    plg_svg2svg(
      [
        {
          src: `${PATH.src}/svg/empty_favicon.svg`,
          dest: `${PATH.dist}/img/empty_favicon.svg`
        },
        {
          src: `${PATH.src}/svg/select-dark.svg`,
          dest: `${PATH.dist}/img/select-dark.svg`
        },
        {
          src: `${PATH.src}/svg/select-light.svg`,
          dest: `${PATH.dist}/img/select-light.svg`
        }
      ],
      svg2svg_opts
    ),

    // SearXNG brand (static)
    plg_svg2png([
      {
        src: `${PATH.brand}/searxng-wordmark.svg`,
        dest: `${PATH.dist}/img/favicon.png`
      },
      {
        src: `${PATH.brand}/searxng.svg`,
        dest: `${PATH.dist}/img/searxng.png`
      }
    ]),

    // -- svg
    plg_svg2svg(
      [
        {
          src: `${PATH.brand}/searxng.svg`,
          dest: `${PATH.dist}/img/searxng.svg`
        },
        {
          src: `${PATH.brand}/img_load_error.svg`,
          dest: `${PATH.dist}/img/img_load_error.svg`
        }
      ],
      svg2svg_opts
    ),

    // -- favicon
    plg_svg2svg(
      [
        {
          src: `${PATH.brand}/searxng-wordmark.svg`,
          dest: `${PATH.dist}/img/favicon.svg`
        }
      ],
      svg2svg_favicon_opts
    ),

    // -- simple templates
    plg_svg2svg(
      [
        {
          src: `${PATH.brand}/searxng-wordmark.svg`,
          dest: `${PATH.templates}/searxng-wordmark.min.svg`
        }
      ],
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
      targets: browserslistToTargets(manifest.browserslist)
    },
    devSourcemap: true
  } // end: css
} satisfies UserConfig;
