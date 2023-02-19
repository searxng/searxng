/* SPDX-License-Identifier: AGPL-3.0-or-later */

module.exports = function (grunt) {

  const eachAsync = require('each-async');

  function file_exists (filepath) {
    // filter function to exit grunt task with error if a (src) file not exists
    if (!grunt.file.exists(filepath)) {
      grunt.fail.fatal('Could not find: ' + filepath, 42);
    } else {
      return true;
    }
  }

  grunt.initConfig({

    _brand: '../../../../src/brand',
    _templates: '../../../templates',

    pkg: grunt.file.readJSON('package.json'),
    watch: {
      scripts: {
        files: ['gruntfile.js', 'src/**'],
        tasks: [
          'eslint',
          'copy',
          'uglify',
          'less',
          'image',
          'svg2png',
          'svg2jinja'
        ]
      }
    },
    eslint: {
      options: {
        overrideConfigFile: '.eslintrc.json',
        failOnError: true,
        fix: grunt.option('fix')
      },
      target: [
        'gruntfile.js',
        'svg4web.svgo.js',
        'src/js/main/*.js',
        'src/js/head/*.js',
      ],
    },
    stylelint: {
      options: {
        formatter: 'unix',
      },
      src: [
        'src/less/**/*.less',
      ]
    },
    copy: {
      js: {
        expand: true,
        cwd: './node_modules',
        dest: './js/',
        flatten: true,
        filter: 'isFile',
        timestamp: true,
        src: [
          './leaflet/dist/leaflet.js',
        ]
      },
      css: {
        expand: true,
        cwd: './node_modules',
        dest: './css/',
        flatten: true,
        filter: 'isFile',
        timestamp: true,
        src: [
          './leaflet/dist/leaflet.css',
        ]
      },
      leaflet_images: {
        expand: true,
        cwd: './node_modules',
        dest: './css/images/',
        flatten: true,
        filter: 'isFile',
        timestamp: true,
        src: [
          './leaflet/dist/images/*.png',
        ]
      },
    },
    uglify: {
      options: {
        output: {
          comments: 'some'
        },
        ie8: false,
        warnings: true,
        compress: false,
        mangle: true,
        sourceMap: {
          includeSources: true
        }
      },
      dist: {
        files: {
          'js/searxng.head.min.js': ['src/js/head/*.js'],
          'js/searxng.min.js': [
            'src/js/main/*.js',
            './node_modules/autocomplete-js/dist/autocomplete.js'
          ]
        }
      }
    },
    less: {
      production: {
        options: {
          paths: ["less"],
          plugins: [
            new (require('less-plugin-clean-css'))()
          ],
          sourceMap: true,
          sourceMapURL: (name) => { const s = name.split('/'); return s[s.length - 1] + '.map'; },
          outputSourceFiles: true,
        },
        files: [
          {
            src: ['src/less/style-ltr.less'],
            dest: 'css/searxng.min.css',
            nonull: true,
            filter: file_exists,
          },
          {
            src: ['src/less/style-rtl.less'],
            dest: 'css/searxng-rtl.min.css',
            nonull: true,
            filter: file_exists,
          },
        ],
      },
    },
    image: {
      svg4web: {
        options: {
          svgo: ['--config', 'svg4web.svgo.js']
        },
        files: {
          '<%= _templates %>/simple/searxng-wordmark.min.svg': '<%= _brand %>/searxng-wordmark.svg',
          'img/searxng.svg': '<%= _brand %>/searxng.svg',
          'img/img_load_error.svg': '<%= _brand %>/img_load_error.svg'
        }
      },
      favicon: {
        options: {
          svgo: ['--config', 'svg4favicon.svgo.js']
        },
        files: {
          'img/favicon.svg': '<%= _brand %>/searxng-wordmark.svg'
        }
      },
    },
    svg2png: {
      favicon: {
        files: {
          'img/favicon.png': '<%= _brand %>/searxng-wordmark.svg',
          'img/searxng.png': '<%= _brand %>/searxng.svg',
        }
      }
    },
    svg2jinja: {
      all: {
        src: {
          'warning': 'node_modules/ionicons/dist/svg/alert-outline.svg',
          'close': 'node_modules/ionicons/dist/svg/close-outline.svg',
          'chevron-up-outline': 'node_modules/ionicons/dist/svg/chevron-up-outline.svg',
          'chevron-right': 'node_modules/ionicons/dist/svg/chevron-forward-outline.svg',
          'chevron-left': 'node_modules/ionicons/dist/svg/chevron-back-outline.svg',
          'menu-outline': 'node_modules/ionicons/dist/svg/settings-outline.svg',
          'ellipsis-vertical-outline': 'node_modules/ionicons/dist/svg/ellipsis-vertical-outline.svg',
          'magnet-outline': 'node_modules/ionicons/dist/svg/magnet-outline.svg',
          'globe-outline': 'node_modules/ionicons/dist/svg/globe-outline.svg',
          'search-outline': 'node_modules/ionicons/dist/svg/search-outline.svg',
          'image-outline': 'node_modules/ionicons/dist/svg/image-outline.svg',
          'play-outline': 'node_modules/ionicons/dist/svg/play-outline.svg',
          'newspaper-outline': 'node_modules/ionicons/dist/svg/newspaper-outline.svg',
          'location-outline': 'node_modules/ionicons/dist/svg/location-outline.svg',
          'musical-notes-outline': 'node_modules/ionicons/dist/svg/musical-notes-outline.svg',
          'layers-outline': 'node_modules/ionicons/dist/svg/layers-outline.svg',
          'school-outline': 'node_modules/ionicons/dist/svg/school-outline.svg',
          'file-tray-full-outline': 'node_modules/ionicons/dist/svg/file-tray-full-outline.svg',
          'people-outline': 'node_modules/ionicons/dist/svg/people-outline.svg',
          'heart-outline': 'node_modules/ionicons/dist/svg/heart-outline.svg',
          'information-circle-outline': 'src/svg/information-circle-outline.svg',
        },
        dest: '../../../templates/simple/icons.html',
      },
    },
  });

  grunt.registerMultiTask('svg2jinja', 'Create Jinja2 macro', function () {
    const ejs = require('ejs'), svgo = require('svgo');
    const icons = {}
    for (const iconName in this.data.src) {
      const svgFileName = this.data.src[iconName];
      try {
        const svgContent = grunt.file.read(svgFileName, { encoding: 'utf8' })
        const svgoResult = svgo.optimize(svgContent, {
          path: svgFileName,
          multipass: true,
          plugins: [
            {
              name: "removeTitle",
            },
            {
              name: "removeXMLNS",
            },
            {
              name: "addAttributesToSVGElement",
              params: {
                attributes: [
                  { "aria-hidden": "true" }
                ]
              }
            }
          ]
        });
        icons[iconName] = svgoResult.data.replace("'", "\\'");
      } catch (err) {
        grunt.log.error(err);
      }
    }
    const template = `{# this file was generated by searx/static/themes/simple/gruntfile.js #}
{%- set icons = {
<% for (const iconName in icons) { %>  '<%- iconName %>':'<%- icons[iconName] %>',
<% } %>
}
-%}

{% macro icon(action, alt) -%}
  {{ icons[action] | replace("ionicon", "ion-icon") | safe }}
{%- endmacro %}

{% macro icon_small(action) -%}
  {{ icons[action] | replace("ionicon", "ion-icon-small") | safe }}
{%- endmacro %}

{% macro icon_big(action, alt) -%}
  {{ icons[action] | replace("ionicon", "ion-icon-big") | safe }}
{%- endmacro %}
`;
    const result = ejs.render(template, { icons });
    grunt.file.write(this.data.dest, result, { encoding: 'utf8' });
    grunt.log.ok(this.data.dest + " created");
  });

  grunt.registerMultiTask('svg2png', 'Convert SVG to PNG', function () {
    const sharp = require('sharp'), done = this.async();
    eachAsync(this.files, async (file, _index, next) => {
      try {
        if (file.src.length != 1) {
          next("this task supports only one source per destination");
        }
        const info = await sharp(file.src[0])
          .png({
            force: true,
            compressionLevel: 9,
            palette: true,
          })
          .toFile(file.dest);
        grunt.log.ok(file.dest + ' created (' + info.size + ' bytes, ' + info.width + 'px * ' + info.height + 'px)');
        next();
      } catch (error) {
        grunt.fatal(error);
        next(error);
      }
    }, error => {
      if (error) {
        grunt.fatal(error);
        done(error);
      } else {
        done();
      }
    });
  });

  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-image');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-stylelint');
  grunt.loadNpmTasks('grunt-eslint');

  grunt.registerTask('test', ['eslint']);

  grunt.registerTask('default', [
    'eslint',
    'stylelint',
    'copy',
    'uglify',
    'less',
    'image',
    'svg2png',
    'svg2jinja',
  ]);
};
