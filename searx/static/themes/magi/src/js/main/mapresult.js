/* SPDX-License-Identifier: AGPL-3.0-or-later */
/* global L */
(function (w, d, searxng) {
  'use strict';

  searxng.ready(function () {
    searxng.on('.searxng_init_map', 'click', function (event) {
      // no more request
      this.classList.remove("searxng_init_map");

      //
      var leaflet_target = this.dataset.leafletTarget;
      var map_lon = parseFloat(this.dataset.mapLon);
      var map_lat = parseFloat(this.dataset.mapLat);
      var map_zoom = parseFloat(this.dataset.mapZoom);
      var map_boundingbox = JSON.parse(this.dataset.mapBoundingbox);
      var map_geojson = JSON.parse(this.dataset.mapGeojson);

      searxng.loadStyle('css/leaflet.css');
      searxng.loadScript('js/leaflet.js', function () {
        var map_bounds = null;
        if (map_boundingbox) {
          var southWest = L.latLng(map_boundingbox[0], map_boundingbox[2]);
          var northEast = L.latLng(map_boundingbox[1], map_boundingbox[3]);
          map_bounds = L.latLngBounds(southWest, northEast);
        }

        // init map
        var map = L.map(leaflet_target);
        // create the tile layer with correct attribution
        var osmMapnikUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
        var osmMapnikAttrib = 'Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors';
        var osmMapnik = new L.TileLayer(osmMapnikUrl, {minZoom: 1, maxZoom: 19, attribution: osmMapnikAttrib});
        var osmWikimediaUrl = 'https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png';
        var osmWikimediaAttrib = 'Wikimedia maps | Maps data © <a href="https://openstreetmap.org">OpenStreetMap contributors</a>';
        var osmWikimedia = new L.TileLayer(osmWikimediaUrl, {minZoom: 1, maxZoom: 19, attribution: osmWikimediaAttrib});
        // init map view
        if (map_bounds) {
          // TODO hack: https://github.com/Leaflet/Leaflet/issues/2021
          // Still useful ?
          setTimeout(function () {
            map.fitBounds(map_bounds, {
              maxZoom: 17
            });
          }, 0);
        } else if (map_lon && map_lat) {
          if (map_zoom) {
            map.setView(new L.latLng(map_lat, map_lon), map_zoom);
          } else {
            map.setView(new L.latLng(map_lat, map_lon), 8);
          }
        }

        map.addLayer(osmMapnik);

        var baseLayers = {
          "OSM Mapnik": osmMapnik,
          "OSM Wikimedia": osmWikimedia,
        };

        L.control.layers(baseLayers).addTo(map);

        if (map_geojson) {
          L.geoJson(map_geojson).addTo(map);
        } /* else if(map_bounds) {
          L.rectangle(map_bounds, {color: "#ff7800", weight: 3, fill:false}).addTo(map);
        } */
      });

      // this event occour only once per element
      event.preventDefault();
    });
  });
})(window, document, window.searxng);
