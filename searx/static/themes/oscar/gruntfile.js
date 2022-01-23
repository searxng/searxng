/*jshint esversion: 6 */
module.exports = function(grunt) {

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    copy: {
      js: {
        expand: true,
        cwd: './node_modules',
        dest: './js/',
        flatten: true,
        filter: 'isFile',
        timestamp: true,
        src: [
          './bootstrap/dist/js/bootstrap.min.js',
          './corejs-typeahead/dist/typeahead.bundle.min.js',
          './jquery/dist/jquery.min.js',
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
          './bootstrap/dist/css/bootstrap-theme.css',
          './bootstrap/dist/css/bootstrap-theme.min.css',
          './bootstrap/dist/css/bootstrap-theme.min.css.map',
          './leaflet/dist/leaflet.css',
        ]
      },
      fonts: {
        expand: true,
        cwd: './node_modules',
        dest: './fonts/',
        flatten: true,
        filter: 'isFile',
        timestamp: true,
        src: [
          './bootstrap/dist/fonts/glyphicons-*.*',
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
      }
    },
    concat: {
      options: {
        separator: ';'
      },
      dist: {
        src: ['src/js/*.js', '../__common__/js/image_layout.js'],
        dest: 'js/searxng.js'
      }
    },
    uglify: {
      options: {
        output: {
	        comments: 'some'
        },
        sourceMap: true,
      },
      dist: {
        files: {
          'js/searxng.min.js': ['<%= concat.dist.dest %>']
        }
      }
    },
    jshint: {
      files: ['gruntfile.js', 'src/js/*.js'],  // files in __common__ are linted by es lint in simple theme
      options: {
        reporterOutput: "",
        esversion: 6,
        // options here to override JSHint defaults
        globals: {
          jQuery: true,
          console: true,
          module: true,
          document: true,
        }
      }
    },
    less: {
      development: {
        options: {
          paths: ["src/less/pointhi", "src/less/logicodev", "src/less/logicodev-dark", "src/less/bootstrap"]
        },
        files: {
          "css/bootstrap.css": "src/less/bootstrap/bootstrap.less",
          "css/pointhi.css": "src/less/pointhi/oscar.less",
          "css/logicodev.css": "src/less/logicodev/oscar.less",
          "css/logicodev-dark.css": "src/less/logicodev-dark/oscar.less"
        }
      },
      production: {
        options: {
          paths: ["src/less/pointhi", "src/less/logicodev", "src/less/logicodev-dark", "src/less/bootstrap"],
          plugins: [
            new (require('less-plugin-clean-css'))()
          ],
          sourceMap: true,
          sourceMapURL: (name) => { const s = name.split('/'); return s[s.length - 1] + '.map';},
          outputSourceFiles: false,
          sourceMapRootpath: '../'
        },
        files: {
          "css/bootstrap.min.css": "css/bootstrap.css",
          "css/leaflet.min.css": "css/leaflet.css",
          "css/pointhi.min.css": "src/less/pointhi/oscar.less",
          "css/logicodev.min.css": "src/less/logicodev/oscar.less",
          "css/logicodev-dark.min.css": "src/less/logicodev-dark/oscar.less"
        }
      },
    },
    watch: {
        scripts: {
            files: ['<%= jshint.files %>'],
            tasks: ['jshint', 'concat', 'uglify']
        },
        oscar_styles: {
            files: ['src/less/pointhi/**/*.less'],
            tasks: ['less:development', 'less:production']
        },
        bootstrap_styles: {
            files: ['less/bootstrap/**/*.less'],
            tasks: ['less:bootstrap']
        }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-less');

  grunt.registerTask('test', ['jshint']);

  grunt.registerTask('default', ['copy', 'jshint', 'concat', 'uglify', 'less']);

  grunt.registerTask('styles', ['less']);

};
