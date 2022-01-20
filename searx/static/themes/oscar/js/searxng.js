/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

window.searxng = (function(d) {
    'use strict';

    //
    d.getElementsByTagName("html")[0].className = "js";

    // add data- properties
    var script = d.currentScript  || (function() {
        var scripts = d.getElementsByTagName('script');
        return scripts[scripts.length - 1];
    })();

    return {
        autocompleter: script.getAttribute('data-autocompleter') === 'true',
        method: script.getAttribute('data-method'),
        translations: JSON.parse(script.getAttribute('data-translations')),
        plugins: JSON.parse(script.getAttribute('data-plugins'))
    };
})(document);
;/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * (C) 2014 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

$(document).ready(function(){
    var original_search_value = '';
    if(searxng.autocompleter) {
        var searchResults = new Bloodhound({
            datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            remote: {
                url: './autocompleter?q=%QUERY',
                wildcard: '%QUERY'
            }
        });
        searchResults.initialize();

        $("#q").on('keydown', function(e) {
			if(e.which == 13) {
                original_search_value = $('#q').val();
			}
		});
        $('#q').typeahead({
            name: 'search-results',
            highlight: false,
            hint: true,
            displayKey: function(result) {
                return result;
            },
            classNames: {
                input: 'tt-input',
                hint: 'tt-hint',
                menu: 'tt-dropdown-menu',
                dataset: 'tt-dataset-search-results',
            },
        }, {
            name: 'autocomplete',
            source: searchResults,
        });
        $('#q').bind('typeahead:select', function(ev, suggestion) {
            if(original_search_value) {
                $('#q').val(original_search_value);
            }
            $("#search_form").submit();
        });
    }
});
;/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * (C) 2014 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

$(document).ready(function(){
    /**
     * focus element if class="autofocus" and id="q"
     */
    $('#q.autofocus').focus();

    /**
     * Empty search bar when click on reset button
     */
    $("#clear_search").click(function () {
	document.getElementById("q").value = "";
    });

    /**
     * select full content on click if class="select-all-on-click"
     */
    $(".select-all-on-click").click(function () {
        $(this).select();
    });

    /**
     * change text during btn-collapse click if possible
     */
    $('.btn-collapse').click(function() {
        var btnTextCollapsed = $(this).data('btn-text-collapsed');
        var btnTextNotCollapsed = $(this).data('btn-text-not-collapsed');

        if(btnTextCollapsed !== '' && btnTextNotCollapsed !== '') {
            if($(this).hasClass('collapsed')) {
                new_html = $(this).html().replace(btnTextCollapsed, btnTextNotCollapsed);
            } else {
                new_html = $(this).html().replace(btnTextNotCollapsed, btnTextCollapsed);
            }
            $(this).html(new_html);
        }
    });

    /**
     * change text during btn-toggle click if possible
     */
    $('.btn-toggle .btn').click(function() {
        var btnClass = 'btn-' + $(this).data('btn-class');
        var btnLabelDefault = $(this).data('btn-label-default');
        var btnLabelToggled = $(this).data('btn-label-toggled');
        if(btnLabelToggled !== '') {
            if($(this).hasClass('btn-default')) {
                new_html = $(this).html().replace(btnLabelDefault, btnLabelToggled);
            } else {
                new_html = $(this).html().replace(btnLabelToggled, btnLabelDefault);
            }
            $(this).html(new_html);
        }
        $(this).toggleClass(btnClass);
        $(this).toggleClass('btn-default');
    });

        /**
     * change text during btn-toggle click if possible
     */
    $('.media-loader').click(function() {
        var target = $(this).data('target');
        var iframe_load = $(target + ' > iframe');
        var srctest = iframe_load.attr('src');
        if(srctest === undefined || srctest === false){
            iframe_load.attr('src', iframe_load.data('src'));
        }
    });

    /**
     * Select or deselect every categories on double clic
     */
    $(".btn-sm").dblclick(function() {
    var btnClass = 'btn-' + $(this).data('btn-class'); // primary
        if($(this).hasClass('btn-default')) {
            $(".btn-sm > input").attr('checked', 'checked');
            $(".btn-sm > input").prop("checked", true);
            $(".btn-sm").addClass(btnClass);
            $(".btn-sm").addClass('active');
            $(".btn-sm").removeClass('btn-default');
        } else {
            $(".btn-sm > input").attr('checked', '');
            $(".btn-sm > input").removeAttr('checked');
            $(".btn-sm > input").checked = false;
            $(".btn-sm").removeClass(btnClass);
            $(".btn-sm").removeClass('active');
            $(".btn-sm").addClass('btn-default');
        }
    });
    $(".nav-tabs").click(function(a) {
        var tabs = $(a.target).parents("ul");
        tabs.children().attr("aria-selected", "false");
        $(a.target).parent().attr("aria-selected", "true");
    });

    /**
     * Layout images according to their sizes
     */
    searxng.image_thumbnail_layout = new searxng.ImageLayout('#main_results', '#main_results .result-images', 'img.img-thumbnail', 15, 3, 200);
    searxng.image_thumbnail_layout.watch();
});
;/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

window.addEventListener('load', function() {
    // Hide infobox toggle if shrunk size already fits all content.
    $('.infobox').each(function() {
        var infobox_body = $(this).find('.infobox_body');
        var total_height = infobox_body.prop('scrollHeight') + infobox_body.find('img.infobox_part').height();
        var max_height = infobox_body.css('max-height').replace('px', '');
        if (total_height <= max_height) {
            $(this).find('.infobox_toggle').hide();
        }
    });
});
;/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * (C) 2014 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

$(document).ready(function(){
    $(".searxng_init_map").on( "click", function( event ) {
        var leaflet_target = $(this).data('leaflet-target');
        var map_lon = $(this).data('map-lon');
        var map_lat = $(this).data('map-lat');
        var map_zoom = $(this).data('map-zoom');
        var map_boundingbox = $(this).data('map-boundingbox');
        var map_geojson = $(this).data('map-geojson');

        if(map_boundingbox) {
            southWest = L.latLng(map_boundingbox[0], map_boundingbox[2]);
            northEast = L.latLng(map_boundingbox[1], map_boundingbox[3]);
            map_bounds = L.latLngBounds(southWest, northEast);
        }

        // change default imagePath
        L.Icon.Default.imagePath =  "./static/themes/oscar/css/images/";

        // init map
        var map = L.map(leaflet_target);

        // create the tile layer with correct attribution
        var osmMapnikUrl='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
        var osmMapnikAttrib='Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors';
        var osmMapnik = new L.TileLayer(osmMapnikUrl, {minZoom: 1, maxZoom: 19, attribution: osmMapnikAttrib});

        var osmWikimediaUrl='https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png';
        var osmWikimediaAttrib = 'Wikimedia maps beta | Maps data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors';
        var osmWikimedia = new L.TileLayer(osmWikimediaUrl, {minZoom: 1, maxZoom: 19, attribution: osmWikimediaAttrib});

        // init map view
        setTimeout(function() {
            if(map_bounds) {
                map.fitBounds(map_bounds, {
                    maxZoom:17
                });
            } else if (map_lon && map_lat) {
                if(map_zoom)
                    map.setView(new L.LatLng(map_lat, map_lon),map_zoom);
                else
                    map.setView(new L.LatLng(map_lat, map_lon),8);
            }    
        }, 0);

        map.addLayer(osmMapnik);

        var baseLayers = {
            "OSM Mapnik": osmMapnik/*,
            "OSM Wikimedia": osmWikimedia*/
        };

        L.control.layers(baseLayers).addTo(map);

        if(map_geojson)
            L.geoJson(map_geojson).addTo(map);
        /*else if(map_bounds)
            L.rectangle(map_bounds, {color: "#ff7800", weight: 3, fill:false}).addTo(map);*/

        // this event occour only once per element
        $( this ).off( event );
    });
});
;/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

$(document).ready(function(){
    let engine_descriptions = null;
    function load_engine_descriptions() {
        if (engine_descriptions == null) {
            $.ajax("engine_descriptions.json", dataType="json").done(function(data) {
                engine_descriptions = data;
                for (const [engine_name, description] of Object.entries(data)) {
                    let elements = $('[data-engine-name="' + engine_name + '"] .description');
                    for(const element of elements) {
                        let source = ' (<i>' + searxng.translations.Source + ':&nbsp;' + description[1] + '</i>)';
                        element.innerHTML = description[0] + source;
                    }
                }
            });
        }
    }

    if (document.querySelector('body[class="preferences_endpoint"]')) {
        $('[data-engine-name]').hover(function() {
            load_engine_descriptions();
        });
    }
});
;/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

$(document).ready(function(){
    $("#allow-all-engines").click(function() {
        $(".onoffswitch-checkbox").each(function() { this.checked = false;});
    });

    $("#disable-all-engines").click(function() {
        $(".onoffswitch-checkbox").each(function() { this.checked = true;});
    });
});

;/**
*
* Google Image Layout v0.0.1
* Description, by Anh Trinh.
* Heavily modified for searx
* https://ptgamr.github.io/2014-09-12-google-image-layout/
* https://ptgamr.github.io/google-image-layout/src/google-image-layout.js
*
* @license Free to use under the MIT License.
*
* @example <caption>Example usage of searxng.ImageLayout class.</caption>
* searxng.image_thumbnail_layout = new searxng.ImageLayout(
*     '#urls',                 // container_selector
*     '#urls .result-images',  // results_selector
*     'img.image_thumbnail',   // img_selector
*     14,                      // verticalMargin
*     6,                       // horizontalMargin
*     200                      // maxHeight
* );
* searxng.image_thumbnail_layout.watch();
*/


(function (w, d) {
  function ImageLayout (container_selector, results_selector, img_selector, verticalMargin, horizontalMargin, maxHeight) {
    this.container_selector = container_selector;
    this.results_selector = results_selector;
    this.img_selector = img_selector;
    this.verticalMargin = verticalMargin;
    this.horizontalMargin = horizontalMargin;
    this.maxHeight = maxHeight;
    this.isAlignDone = true;
  }

  /**
  * Get the height that make all images fit the container
  *
  * width = w1 + w2 + w3 + ... = r1*h + r2*h + r3*h + ...
  *
  * @param  {[type]} images the images to be calculated
  * @param  {[type]} width  the container witdth
  * @param  {[type]} margin the margin between each image
  *
  * @return {[type]}        the height
  */
  ImageLayout.prototype._getHeigth = function (images, width) {
    var i, img;
    var r = 0;

    for (i = 0; i < images.length; i++) {
      img = images[i];
      if ((img.naturalWidth > 0) && (img.naturalHeight > 0)) {
        r += img.naturalWidth / img.naturalHeight;
      } else {
        // assume that not loaded images are square
        r += 1;
      }
    }

    return (width - images.length * this.verticalMargin) / r; // have to round down because Firefox will automatically roundup value with number of decimals > 3
  };

  ImageLayout.prototype._setSize = function (images, height) {
    var i, img, imgWidth;
    var imagesLength = images.length, resultNode;

    for (i = 0; i < imagesLength; i++) {
      img = images[i];
      if ((img.naturalWidth > 0) && (img.naturalHeight > 0)) {
        imgWidth = height * img.naturalWidth / img.naturalHeight;
      } else {
        // not loaded image : make it square as _getHeigth said it
        imgWidth = height;
      }
      img.style.width = imgWidth + 'px';
      img.style.height = height + 'px';
      img.style.marginLeft = this.horizontalMargin + 'px';
      img.style.marginTop = this.horizontalMargin + 'px';
      img.style.marginRight = this.verticalMargin - 7 + 'px'; // -4 is the negative margin of the inline element
      img.style.marginBottom = this.verticalMargin - 7 + 'px';
      resultNode = img.parentNode.parentNode;
      if (!resultNode.classList.contains('js')) {
        resultNode.classList.add('js');
      }
    }
  };

  ImageLayout.prototype._alignImgs = function (imgGroup) {
    var isSearching, slice, i, h;
    var containerElement = d.querySelector(this.container_selector);
    var containerCompStyles = window.getComputedStyle(containerElement);
    var containerPaddingLeft = parseInt(containerCompStyles.getPropertyValue('padding-left'), 10);
    var containerPaddingRight = parseInt(containerCompStyles.getPropertyValue('padding-right'), 10);
    var containerWidth = containerElement.clientWidth - containerPaddingLeft - containerPaddingRight;

    while (imgGroup.length > 0) {
      isSearching = true;
      for (i = 1; i <= imgGroup.length && isSearching; i++) {
        slice = imgGroup.slice(0, i);
        h = this._getHeigth(slice, containerWidth);
        if (h < this.maxHeight) {
          this._setSize(slice, h);
          // continue with the remaining images
          imgGroup = imgGroup.slice(i);
          isSearching = false;
        }
      }
      if (isSearching) {
        this._setSize(slice, Math.min(this.maxHeight, h));
        break;
      }
    }
  };

  ImageLayout.prototype.align = function () {
    var i;
    var results_selectorNode = d.querySelectorAll(this.results_selector);
    var results_length = results_selectorNode.length;
    var previous = null;
    var current = null;
    var imgGroup = [];

    for (i = 0; i < results_length; i++) {
      current = results_selectorNode[i];
      if (current.previousElementSibling !== previous && imgGroup.length > 0) {
        // the current image is not connected to previous one
        // so the current image is the start of a new group of images.
        // so call _alignImgs to align the current group
        this._alignImgs(imgGroup);
        // and start a new empty group of images
        imgGroup = [];
      }
      // add the current image to the group (only the img tag)
      imgGroup.push(current.querySelector(this.img_selector));
      // update the previous variable
      previous = current;
    }
    // align the remaining images
    if (imgGroup.length > 0) {
      this._alignImgs(imgGroup);
    }
  };

  ImageLayout.prototype.watch = function () {
    var i, img;
    var obj = this;
    var results_nodes = d.querySelectorAll(this.results_selector);
    var results_length = results_nodes.length;

    function img_load_error (event) {
      // console.log("ERROR can't load: " + event.originalTarget.src);
      event.originalTarget.src = w.searxng.static_path + w.searxng.theme.img_load_error;
    }

    function throttleAlign () {
      if (obj.isAlignDone) {
        obj.isAlignDone = false;
        setTimeout(function () {
          obj.align();
          obj.isAlignDone = true;
        }, 100);
      }
    }

    // https://developer.mozilla.org/en-US/docs/Web/API/Window/pageshow_event
    w.addEventListener('pageshow', throttleAlign);
    // https://developer.mozilla.org/en-US/docs/Web/API/FileReader/load_event
    w.addEventListener('load', throttleAlign);
    // https://developer.mozilla.org/en-US/docs/Web/API/Window/resize_event
    w.addEventListener('resize', throttleAlign);

    for (i = 0; i < results_length; i++) {
      img = results_nodes[i].querySelector(this.img_selector);
      if (img !== null && img !== undefined) {
        img.addEventListener('load', throttleAlign);
        // https://developer.mozilla.org/en-US/docs/Web/API/GlobalEventHandlers/onerror
        img.addEventListener('error', throttleAlign);
        if (w.searxng.theme.img_load_error) {
          img.addEventListener('error', img_load_error, {once: true});
        }
      }
    }
  };

  w.searxng.ImageLayout = ImageLayout;

}(window, document));
;if (searxng.plugins['searx.plugins.infinite_scroll']) {
    function hasScrollbar() {
        var root = document.compatMode=='BackCompat'? document.body : document.documentElement;
        return root.scrollHeight>root.clientHeight;
    }

    function loadNextPage() {
        var formData = $('#pagination form:last').serialize();
        if (formData) {
            $('#pagination').html('<div class="loading-spinner"></div>');
            $.ajax({
                type: "POST",
                url: $('#search_form').prop('action'),
                data: formData,
                dataType: 'html',
                success: function(data) {
                    var body = $(data);
                    $('#pagination').remove();
                    $('#main_results').append('<hr/>');
                    $('#main_results').append(body.find('.result'));
                    $('#main_results').append(body.find('#pagination'));
                    if(!hasScrollbar()) {
                        loadNextPage();
                    }
                }
            });
        }
    }

    $(document).ready(function() {
        var win = $(window);
        if(!hasScrollbar()) {
            loadNextPage();
        }
        win.scroll(function() {
            $("#pagination button").css("visibility", "hidden");
            if ($(document).height() - win.height() - win.scrollTop() < 150) {
                loadNextPage();
            }
        });
    });

    const style = document.createElement('style');
    style.textContent = `
    @keyframes rotate-forever {
        0%   { transform: rotate(0deg) }
        100% { transform: rotate(360deg) }
    }
    .loading-spinner {
        animation-duration: 0.75s;
        animation-iteration-count: infinite;
        animation-name: rotate-forever;
        animation-timing-function: linear;
        height: 30px;
        width: 30px;
        border: 8px solid #666;
        border-right-color: transparent;
        border-radius: 50% !important;
        margin: 0 auto;
    }
    #pagination button {
        visibility: hidden;
    }
    `;
    document.head.append(style);
}
;if (searxng.plugins['searx.plugins.search_on_category_select']) {
    $(document).ready(function() {
        if($('#q').length) {
            $('#categories label').click(function(e) {
                $('#categories input[type="checkbox"]').each(function(i, checkbox) {
                    $(checkbox).prop('checked', false);
                });
                $(document.getElementById($(this).attr("for"))).prop('checked', true);
                if($('#q').val()) {
                    if (getHttpRequest() == "GET") {
                        $('#search_form').attr('action', $('#search_form').serialize());
                    }
                    $('#search_form').submit();
                }
                return false;
            });
            $('#time-range').change(function(e) {
                if($('#q').val()) {
                    if (getHttpRequest() == "GET") {
                        $('#search_form').attr('action', $('#search_form').serialize());
                    }
                    $('#search_form').submit();
                }
            });
            $('#language').change(function(e) {
                if($('#q').val()) {
                    if (getHttpRequest() == "GET") {
                        $('#search_form').attr('action', $('#search_form').serialize());
                    }
                    $('#search_form').submit();
                }
            });
        }
    });

    function getHttpRequest() {
        httpRequest = "POST";
        urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('method')) {
            httpRequest = urlParams.get('method');
        }
        return httpRequest;
    }
}
;if (searxng.plugins['searx.plugins.vim_hotkeys']) {
    $(document).ready(function() {
        highlightResult('top')();

        $('.result').on('click', function() {
            highlightResult($(this))();
        });

        var vimKeys = {
            27: {
                key: 'Escape',
                fun: removeFocus,
                des: 'remove focus from the focused input',
                cat: 'Control'
            },
            73: {
                key: 'i',
                fun: searchInputFocus,
                des: 'focus on the search input',
                cat: 'Control'
            },
            66: {
                key: 'b',
                fun: scrollPage(-window.innerHeight),
                des: 'scroll one page up',
                cat: 'Navigation'
            },
            70: {
                key: 'f',
                fun: scrollPage(window.innerHeight),
                des: 'scroll one page down',
                cat: 'Navigation'
            },
            85: {
                key: 'u',
                fun: scrollPage(-window.innerHeight / 2),
                des: 'scroll half a page up',
                cat: 'Navigation'
            },
            68: {
                key: 'd',
                fun: scrollPage(window.innerHeight / 2),
                des: 'scroll half a page down',
                cat: 'Navigation'
            },
            71: {
                key: 'g',
                fun: scrollPageTo(-document.body.scrollHeight, 'top'),
                des: 'scroll to the top of the page',
                cat: 'Navigation'
            },
            86: {
                key: 'v',
                fun: scrollPageTo(document.body.scrollHeight, 'bottom'),
                des: 'scroll to the bottom of the page',
                cat: 'Navigation'
            },
            75: {
                key: 'k',
                fun: highlightResult('up'),
                des: 'select previous search result',
                cat: 'Results'
            },
            74: {
                key: 'j',
                fun: highlightResult('down'),
                des: 'select next search result',
                cat: 'Results'
            },
            80: {
                key: 'p',
                fun: pageButtonClick(0),
                des: 'go to previous page',
                cat: 'Results'
            },
            78: {
                key: 'n',
                fun: pageButtonClick(1),
                des: 'go to next page',
                cat: 'Results'
            },
            79: {
                key: 'o',
                fun: openResult(false),
                des: 'open search result',
                cat: 'Results'
            },
            84: {
                key: 't',
                fun: openResult(true),
                des: 'open the result in a new tab',
                cat: 'Results'
            },
            82: {
                key: 'r',
                fun: reloadPage,
                des: 'reload page from the server',
                cat: 'Control'
            },
            72: {
                key: 'h',
                fun: toggleHelp,
                des: 'toggle help window',
                cat: 'Other'
            }
        };

        $(document).keydown(function(e) {
            // check for modifiers so we don't break browser's hotkeys
            if (vimKeys.hasOwnProperty(e.keyCode)
                && !e.ctrlKey
                && !e.altKey
                && !e.shiftKey
                && !e.metaKey)
            {
                if (e.keyCode === 27) {
                    if (e.target.tagName.toLowerCase() === 'input') {
                        vimKeys[e.keyCode].fun();
                    }
                } else {
                    if (e.target === document.body) {
                        e.preventDefault();
                        vimKeys[e.keyCode].fun();
                    }
                }
            }
        });

        function nextResult(current, direction) {
            var next = current[direction]();
            while (!next.is('.result') && next.length !== 0) {
                next = next[direction]();
            }
            return next
        }

        function highlightResult(which) {
            return function() {
                var current = $('.result[data-vim-selected]');
                if (current.length === 0) {
                    current = $('.result:first');
                    if (current.length === 0) {
                        return;
                    }
                }

                var next;

                if (typeof which !== 'string') {
                    next = which;
                } else {
                    switch (which) {
                        case 'visible':
                            var top = $(window).scrollTop();
                            var bot = top + $(window).height();
                            var results = $('.result');

                            for (var i = 0; i < results.length; i++) {
                                next = $(results[i]);
                                var etop = next.offset().top;
                                var ebot = etop + next.height();

                                if ((ebot <= bot) && (etop > top)) {
                                    break;
                                }
                            }
                            break;
                        case 'down':
                            next = nextResult(current, 'next');
                            if (next.length === 0) {
                                next = $('.result:first');
                            }
                            break;
                        case 'up':
                            next = nextResult(current, 'prev');
                            if (next.length === 0) {
                                next = $('.result:last');
                            }
                            break;
                        case 'bottom':
                            next = $('.result:last');
                            break;
                        case 'top':
                        default:
                            next = $('.result:first');
                    }
                }

                if (next) {
                    current.removeAttr('data-vim-selected').removeClass('well well-sm');
                    next.attr('data-vim-selected', 'true').addClass('well well-sm');
                    scrollPageToSelected();
                }
            }
        }

        function reloadPage() {
            document.location.reload(false);
        }

        function removeFocus() {
            if (document.activeElement) {
                document.activeElement.blur();
            }
        }

        function pageButtonClick(num) {
            return function() {
                var buttons = $('div#pagination button[type="submit"]');
                if (buttons.length !== 2) {
                    console.log('page navigation with this theme is not supported');
                    return;
                }
                if (num >= 0 && num < buttons.length) {
                    buttons[num].click();
                } else {
                    console.log('pageButtonClick(): invalid argument');
                }
            }
        }

        function scrollPageToSelected() {
            var sel = $('.result[data-vim-selected]');
            if (sel.length !== 1) {
                return;
            }

            var wnd = $(window);

            var wtop = wnd.scrollTop();
            var etop = sel.offset().top;

            var offset = 30;

            if (wtop > etop) {
                wnd.scrollTop(etop - offset);
            } else  {
                var ebot = etop + sel.height();
                var wbot = wtop + wnd.height();

                if (wbot < ebot) {
                    wnd.scrollTop(ebot - wnd.height() + offset);
                }
            }
        }

        function scrollPage(amount) {
            return function() {
                window.scrollBy(0, amount);
                highlightResult('visible')();
            }
        }

        function scrollPageTo(position, nav) {
            return function() {
                window.scrollTo(0, position);
                highlightResult(nav)();
            }
        }

        function searchInputFocus() {
            $('input#q').focus();
        }

        function openResult(newTab) {
            return function() {
                var link = $('.result[data-vim-selected] .result_header a');
                if (link.length) {
                    var url = link.attr('href');
                    if (newTab) {
                        window.open(url);
                    } else {
                        window.location.href = url;
                    }
                }
            };
        }

        function toggleHelp() {
            var helpPanel = $('#vim-hotkeys-help');
            if (helpPanel.length) {
                helpPanel.toggleClass('hidden');
                return;
            }

            var categories = {};

            for (var k in vimKeys) {
                var key = vimKeys[k];
                categories[key.cat] = categories[key.cat] || [];
                categories[key.cat].push(key);
            }

            var sorted = Object.keys(categories).sort(function(a, b) {
                return categories[b].length - categories[a].length;
            });

            if (sorted.length === 0) {
                return;
            }

            var html = '<div id="vim-hotkeys-help" class="well vim-hotkeys-help">';
            html += '<div class="container-fluid">';

            html += '<div class="row">';
            html += '<div class="col-sm-12">';
            html += '<h3>How to navigate searx with Vim-like hotkeys</h3>';
            html += '</div>'; // col-sm-12
            html += '</div>'; // row

            for (var i = 0; i < sorted.length; i++) {
                var cat = categories[sorted[i]];

                var lastCategory = i === (sorted.length - 1);
                var first = i % 2 === 0;

                if (first) {
                    html += '<div class="row dflex">';
                }
                html += '<div class="col-sm-' + (first && lastCategory ? 12 : 6) + ' dflex">';

                html += '<div class="panel panel-default iflex">';
                html += '<div class="panel-heading">' + cat[0].cat + '</div>';
                html += '<div class="panel-body">';
                html += '<ul class="list-unstyled">';

                for (var cj in cat) {
                    html += '<li><kbd>' + cat[cj].key + '</kbd> ' + cat[cj].des + '</li>';
                }

                html += '</ul>';
                html += '</div>'; // panel-body
                html += '</div>'; // panel
                html += '</div>'; // col-sm-*

                if (!first || lastCategory) {
                    html += '</div>'; // row
                }
            }

            html += '</div>'; // container-fluid
            html += '</div>'; // vim-hotkeys-help

            $('body').append(html);
        }
    });

    const style = document.createElement('style');
    style.textContent = `
    .vim-hotkeys-help {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 9999999;
        overflow-y: auto;
        max-height: 80%;
        box-shadow: 0 0 1em;
    }

    .dflex {
        display: -webkit-box;  /* OLD - iOS 6-, Safari 3.1-6 */
        display: -moz-box;     /* OLD - Firefox 19- (buggy but mostly works) */
        display: -ms-flexbox;  /* TWEENER - IE 10 */
        display: -webkit-flex; /* NEW - Chrome */
        display: flex;         /* NEW, Spec - Opera 12.1, Firefox 20+ */
    }

    .iflex {
        -webkit-box-flex: 1; /* OLD - iOS 6-, Safari 3.1-6 */
        -moz-box-flex: 1;    /* OLD - Firefox 19- */
        -webkit-flex: 1;     /* Chrome */
        -ms-flex: 1;         /* IE 10 */
        flex: 1;             /* NEW, Spec - Opera 12.1, Firefox 20+ */
    }
    `;
    document.head.append(style);
}
