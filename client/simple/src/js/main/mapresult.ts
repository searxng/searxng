// SPDX-License-Identifier: AGPL-3.0-or-later

import { listen } from "../core/toolkit.ts";

listen("click", ".searxng_init_map", async function (this: HTMLElement, event: Event) {
  event.preventDefault();
  this.classList.remove("searxng_init_map");

  const {
    View,
    OlMap,
    TileLayer,
    VectorLayer,
    OSM,
    VectorSource,
    Style,
    Stroke,
    Fill,
    Circle,
    fromLonLat,
    GeoJSON,
    Feature,
    Point
  } = await import("../pkg/ol.ts");
  void import("ol/ol.css");

  const { leafletTarget: target, mapLon, mapLat, mapGeojson } = this.dataset;

  const lon = Number.parseFloat(mapLon || "0");
  const lat = Number.parseFloat(mapLat || "0");
  const view = new View({ maxZoom: 16, enableRotation: false });
  const map = new OlMap({
    target: target,
    layers: [new TileLayer({ source: new OSM({ maxZoom: 16 }) })],
    view: view
  });

  try {
    const markerSource = new VectorSource({
      features: [
        new Feature({
          geometry: new Point(fromLonLat([lon, lat]))
        })
      ]
    });

    const markerLayer = new VectorLayer({
      source: markerSource,
      style: new Style({
        image: new Circle({
          radius: 6,
          fill: new Fill({ color: "#3050ff" })
        })
      })
    });

    map.addLayer(markerLayer);
  } catch (error) {
    console.error("Failed to create marker layer:", error);
  }

  if (mapGeojson) {
    try {
      const geoSource = new VectorSource({
        features: new GeoJSON().readFeatures(JSON.parse(mapGeojson), {
          dataProjection: "EPSG:4326",
          featureProjection: "EPSG:3857"
        })
      });

      const geoLayer = new VectorLayer({
        source: geoSource,
        style: new Style({
          stroke: new Stroke({ color: "#3050ff", width: 2 }),
          fill: new Fill({ color: "#3050ff33" })
        })
      });

      map.addLayer(geoLayer);

      view.fit(geoSource.getExtent(), { padding: [20, 20, 20, 20] });
    } catch (error) {
      console.error("Failed to create GeoJSON layer:", error);
    }
  }
});
