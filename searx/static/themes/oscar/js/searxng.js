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
        infinite_scroll: script.getAttribute('data-infinite-scroll') === 'true',
        method: script.getAttribute('data-method'),
        translations: JSON.parse(script.getAttribute('data-translations'))
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
    this.trottleCallToAlign = null;
    this.alignAfterThrotteling = false;
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
      img.setAttribute('width', Math.round(imgWidth));
      img.setAttribute('height', Math.round(height));
      img.style.marginLeft = Math.round(this.horizontalMargin) + 'px';
      img.style.marginTop = Math.round(this.horizontalMargin) + 'px';
      img.style.marginRight = Math.round(this.verticalMargin - 7) + 'px'; // -4 is the negative margin of the inline element
      img.style.marginBottom = Math.round(this.verticalMargin - 7) + 'px';
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

  ImageLayout.prototype.throttleAlign = function () {
    var obj = this;
    if (obj.trottleCallToAlign) {
      obj.alignAfterThrotteling = true;
    } else {
      obj.alignAfterThrotteling = false;
      obj.align();
      obj.trottleCallToAlign = setTimeout(function () {
        if (obj.alignAfterThrotteling) {
          obj.align();
        }
        obj.alignAfterThrotteling = false;
        obj.trottleCallToAlign = null;
      }, 20);
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

  ImageLayout.prototype._monitorImages = function () {
    var i, img;
    var objthrottleAlign = this.throttleAlign.bind(this);
    var results_nodes = d.querySelectorAll(this.results_selector);
    var results_length = results_nodes.length;

    function img_load_error (event) {
      // console.log("ERROR can't load: " + event.originalTarget.src);
      event.originalTarget.src = w.searxng.static_path + w.searxng.theme.img_load_error;
    }

    for (i = 0; i < results_length; i++) {
      img = results_nodes[i].querySelector(this.img_selector);
      if (img !== null && img !== undefined && !img.classList.contains('aligned')) {
        img.addEventListener('load', objthrottleAlign);
        // https://developer.mozilla.org/en-US/docs/Web/API/GlobalEventHandlers/onerror
        img.addEventListener('error', objthrottleAlign);
        img.addEventListener('timeout', objthrottleAlign);
        if (w.searxng.theme.img_load_error) {
          img.addEventListener('error', img_load_error, {once: true});
        }
        img.classList.add('aligned');
      }
    }
  };

  ImageLayout.prototype.watch = function () {
    var objthrottleAlign = this.throttleAlign.bind(this);

    // https://developer.mozilla.org/en-US/docs/Web/API/Window/pageshow_event
    w.addEventListener('pageshow', objthrottleAlign);
    // https://developer.mozilla.org/en-US/docs/Web/API/FileReader/load_event
    w.addEventListener('load', objthrottleAlign);
    // https://developer.mozilla.org/en-US/docs/Web/API/Window/resize_event
    w.addEventListener('resize', objthrottleAlign);

    this._monitorImages();

    var obj = this;

    let observer = new MutationObserver(entries => {
      let newElement = false;
      for (let i = 0; i < entries.length; i++) {
        if (entries[i].addedNodes.length > 0 && entries[i].addedNodes[0].classList.contains('result')) {
          newElement = true;
          break;
        }
      }
      if (newElement) {
        obj._monitorImages();
      }
    });
    observer.observe(d.querySelector(this.container_selector), {
      childList: true,
      subtree: true,
      attributes: false,
      characterData: false,
    });
  };

  w.searxng.ImageLayout = ImageLayout;

}(window, document));
;/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

$(document).ready(function() {
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

    if (searxng.infinite_scroll) {
        var win = $(window);
        $("html").addClass('infinite_scroll');
        if(!hasScrollbar()) {
            loadNextPage();
        }
        win.on('scroll', function() {
            if ($(document).height() - win.height() - win.scrollTop() < 150) {
                loadNextPage();
            }
        });
    }

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

