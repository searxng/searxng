/**
* searx is free software: you can redistribute it and/or modify
* it under the terms of the GNU Affero General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* searx is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU Affero General Public License for more details.
*
* You should have received a copy of the GNU Affero General Public License
* along with searx. If not, see < http://www.gnu.org/licenses/ >.
*
* (C) 2014 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
* (C) 2017 by Alexandre Flament, <alex@al-f.net>
*/
(function (w, d, searx) {
  'use strict';

  searx.ready(function () {
    searx.on('.searx_init_map', 'click', function(event) {
      // no more request
      this.classList.remove("searx_init_map");

      //
      var leaflet_target = this.dataset.leafletTarget;
      var map_lon = parseFloat(this.dataset.mapLon);
      var map_lat = parseFloat(this.dataset.mapLat);
      var map_zoom = parseFloat(this.dataset.mapZoom);
      var map_boundingbox = JSON.parse(this.dataset.mapBoundingbox);
      var map_geojson = JSON.parse(this.dataset.mapGeojson);

      searx.loadStyle('leaflet/leaflet.css');
      searx.loadScript('leaflet/leaflet.js', function() {
        var map_bounds = null;
        if(map_boundingbox) {
          var southWest = L.latLng(map_boundingbox[0], map_boundingbox[2]);
          var northEast = L.latLng(map_boundingbox[1], map_boundingbox[3]);
          map_bounds = L.latLngBounds(southWest, northEast);
        }

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
        if(map_bounds) {
          // TODO hack: https://github.com/Leaflet/Leaflet/issues/2021
          // Still useful ?
          setTimeout(function () {
            map.fitBounds(map_bounds, {
              maxZoom:17
            });
          }, 0);
        } else if (map_lon && map_lat) {
          if(map_zoom) {
            map.setView(new L.latLng(map_lat, map_lon),map_zoom);
          } else {
            map.setView(new L.latLng(map_lat, map_lon),8);
          }
        }

        map.addLayer(osmMapnik);

        var baseLayers = {
          "OSM Mapnik": osmMapnik/*,
          "OSM Wikimedia": osmWikimedia*/
        };

        L.control.layers(baseLayers).addTo(map);

        if(map_geojson) {
          L.geoJson(map_geojson).addTo(map);
        } /*else if(map_bounds) {
          L.rectangle(map_bounds, {color: "#ff7800", weight: 3, fill:false}).addTo(map);
        }*/
      });

      // this event occour only once per element
      event.preventDefault();
    });
  });
})(window, document, window.searx);
