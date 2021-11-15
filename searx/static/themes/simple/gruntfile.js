/*jshint esversion: 6 */

module.exports = function(grunt) {

  const path = require('path');

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    watch: {
      scripts: {
        files: ['gruntfile.js', 'src/**'],
        tasks: ['eslint', 'copy', 'concat', 'svg2jinja', 'uglify', 'image', 'less:development', 'less:production']
      }
    },
    eslint: {
      options: {
        configFile: '.eslintrc.json',
        failOnError: false
      },
      target: [
        'svg4web.svgo.js',
        'src/js/main/*.js',
        'src/js/head/*.js',
        '../__common__/js/*.js'
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
    concat: {
      head_and_body: {
        options: {
          separator: ';'
        },
        files: {
          'js/searxng.head.js': ['src/js/head/*.js'],
          'js/searxng.js': ['src/js/main/*.js', '../__common__/js/*.js', './node_modules/autocomplete-js/dist/autocomplete.js']
        }
      }
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
        sourceMap: true
      },
      dist: {
        files: {
          'js/searxng.head.min.js': ['js/searxng.head.js'],
          'js/searxng.min.js': ['js/searxng.js']
        }
      }
    },
    image: {
      svg4web: {
        options: {
          svgo: ['--config', 'svg4web.svgo.js']
        },
        files: {
          '../../../templates/__common__/searxng-wordmark.min.svg': 'src/svg/searxng-wordmark.svg'
        }
      }
    },
    less: {
      development: {
        options: {
          paths: ["less"],
        },
        files: {
          "css/searxng.css": "src/less/style.less",
          "css/searxng-rtl.css": "src/less/style-rtl.less"
        }
      },
      production: {
        options: {
          paths: ["less"],
          plugins: [
            new (require('less-plugin-clean-css'))()
          ],
          sourceMap: true,
          sourceMapURL: (name) => { const s = name.split('/'); return s[s.length - 1] + '.map';},
          outputSourceFiles: false,
          sourceMapRootpath: '../',
        },
        files: {
          "css/searxng.min.css": "src/less/style.less",
          "css/searxng-rtl.min.css": "src/less/style-rtl.less"
        }
      },
    },
    svg2jinja: {
      all: {
        src: {
          'warning': 'node_modules/ionicons/dist/svg/alert-outline.svg',
          'close': 'node_modules/ionicons/dist/svg/close-outline.svg',
          'chevron-up-outline': 'node_modules/ionicons/dist/svg/chevron-up-outline.svg',
          'chevron-right': 'node_modules/ionicons/dist/svg/chevron-forward-outline.svg',
          'chevron-left': 'node_modules/ionicons/dist/svg/chevron-back-outline.svg',
          'menu-outline': 'node_modules/ionicons/dist/svg/menu-outline.svg',
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
        },
        dest: '../../../templates/simple/icons.html',
      },
    },
  });


  grunt.registerMultiTask('svg2jinja', 'Create Jinja2 macro', function() {
    const ejs = require('ejs'), svgo = require('svgo');
    const icons = {}
    for(const iconName in this.data.src) {
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

  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-image');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-stylelint');
  grunt.loadNpmTasks('grunt-eslint');

  grunt.registerTask('test', ['jshint']);

  grunt.registerTask('default', [
    'eslint',
    'stylelint',
    'copy',
    'concat',
    'svg2jinja',
    'uglify',
    'image',
    'less:development',
    'less:production'
  ]);
};
