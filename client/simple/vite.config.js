/**
 * CONFIG: https://vite.dev/config/
 */

import { resolve } from "node:path";
import { defineConfig } from "vite";
import { viteStaticCopy } from "vite-plugin-static-copy";


const ROOT = "../..";  // root of the git reposetory

const PATH = {

  dist: resolve(ROOT, "searx/static/themes/simple"),
  // dist: resolve(ROOT, "client/simple/dist"),

  src: "src",
  modules: "node_modules",
  brand: "src/brand",
  static: resolve(ROOT, "client/simple/static"),
  leaflet: resolve(ROOT, "client/simple/node_modules/leaflet/dist"),
  templates: resolve(ROOT, "searx/templates/simple"),
};


};


export default defineConfig({

  root: PATH.src,
  mode: "production",
  // mode: "development",

  // FIXME: missing CCS sourcemaps!!
  // see: https://github.com/vitejs/vite/discussions/13845#discussioncomment-11992084
  //
  // what I have tried so far (see config below):
  //
  // - build.sourcemap
  // - esbuild.sourcemap
  // - css.preprocessorOptions.less.sourceMap

  css: {
    devSourcemap: true,
    preprocessorOptions: {
      less: {
        // FIXME: missing CCS sourcemaps!!
        sourceMap: {
          outputSourceFiles: true,
          sourceMapURL: (name) => { const s = name.split('/'); return s[s.length - 1] + '.map'; },
        },
        // env: 'development',
        // relativeUrls: true,
        // javascriptEnabled: true,
      },
    },
  },  // end: css

  esbuild : {
    // FIXME: missing CCS sourcemaps!!
    sourcemap: true
  },

  build: {
    manifest: "manifest.json",
    emptyOutDir: true,
    assetsDir: "",
    outDir: PATH.dist,

    // FIXME: missing CCS sourcemaps!!
    sourcemap: true,

    // https://vite.dev/config/build-options.html#build-cssminify
    cssMinify: true,
    // cssMinify: "esbuild",
    minify: "esbuild",

    rollupOptions: {
      input: {

        // build CSS files
        "css/searxng.min.css": PATH.src + "/less/style-ltr.less",
        "css/searxng-rtl.min.css": PATH.src + "/less/style-rtl.less",
        "css/rss.min.css": PATH.src + "/less/rss.less",

        // build JS files
        "js/searxng.head.min": PATH.src + "/js/searxng.head.js",
        "js/searxng.min": PATH.src + "/js/searxng.js",

      },

      // file naming conventions / pathnames are relative to outDir (PATH.dist)
      output: {
        entryFileNames: "[name].js",
        chunkFileNames: "[name].js",
        assetFileNames: "[name].[ext]",
        // Vite does not support "rollupOptions.output.sourcemap".
        // Please use "build.sourcemap" instead.
        // sourcemap: true,
      },

    },
  },  // end: build

  plugins: [

    // Leaflet

    viteStaticCopy({
      targets: [
        { src: PATH.leaflet + "/leaflet.{js,js.map}", dest: PATH.dist + "/js" },
        { src: PATH.leaflet + "/images/*.png", dest: PATH.dist + "/css/images/" },
        { src: PATH.leaflet + "/*.{css,css.map}", dest: PATH.dist + "/css" },
        { src: PATH.static + "/**/*", dest: PATH.dist },
      ]
    })
  ],
  ] // end: plugins

});
