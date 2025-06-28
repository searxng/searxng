/* SPDX-License-Identifier: AGPL-3.0-or-later */
/* global L */
((_w, _d, searxng) => {
  searxng.ready(() => {
    searxng.on(".searxng_init_map", "click", function (event) {
      // no more request
      this.classList.remove("searxng_init_map");

      //
      const leaflet_target = this.dataset.leafletTarget;
      const map_lon = parseFloat(this.dataset.mapLon);
      const map_lat = parseFloat(this.dataset.mapLat);
      const map_zoom = parseFloat(this.dataset.mapZoom);
      const map_boundingbox = JSON.parse(this.dataset.mapBoundingbox);
      const map_geojson = JSON.parse(this.dataset.mapGeojson);

      searxng.loadStyle("css/leaflet.css");
      searxng.loadScript("js/leaflet.js", () => {
        let map_bounds = null;
        if (map_boundingbox) {
          const southWest = L.latLng(map_boundingbox[0], map_boundingbox[2]);
          const northEast = L.latLng(map_boundingbox[1], map_boundingbox[3]);
          map_bounds = L.latLngBounds(southWest, northEast);
        }

        // init map
        const map = L.map(leaflet_target);
        // create the tile layer with correct attribution
        const osmMapnikUrl = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
        const osmMapnikAttrib = 'Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors';
        const osmMapnik = new L.TileLayer(osmMapnikUrl, { minZoom: 1, maxZoom: 19, attribution: osmMapnikAttrib });
        const osmWikimediaUrl = "https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png";
        const osmWikimediaAttrib =
          'Wikimedia maps | Maps data © <a href="https://openstreetmap.org">OpenStreetMap contributors</a>';
        const osmWikimedia = new L.TileLayer(osmWikimediaUrl, {
          minZoom: 1,
          maxZoom: 19,
          attribution: osmWikimediaAttrib
        });
        // init map view
        if (map_bounds) {
          // TODO hack: https://github.com/Leaflet/Leaflet/issues/2021
          // Still useful ?
          setTimeout(() => {
            map.fitBounds(map_bounds, {
              maxZoom: 17
            });
          }, 0);
        } else if (map_lon && map_lat) {
          if (map_zoom) {
            map.setView(new L.LatLng(map_lat, map_lon), map_zoom);
          } else {
            map.setView(new L.LatLng(map_lat, map_lon), 8);
          }
        }

        map.addLayer(osmMapnik);

        const baseLayers = {
          "OSM Mapnik": osmMapnik,
          "OSM Wikimedia": osmWikimedia
        };

        L.control.layers(baseLayers).addTo(map);

        if (map_geojson) {
          L.geoJson(map_geojson).addTo(map);
        } /* else if(map_bounds) {
          L.rectangle(map_bounds, {color: "#ff7800", weight: 3, fill:false}).addTo(map);
        } */
      });

      // this event occur only once per element
      event.preventDefault();
    });
  });
})(window, document, window.searxng);
