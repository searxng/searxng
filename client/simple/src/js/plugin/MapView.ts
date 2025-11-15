// SPDX-License-Identifier: AGPL-3.0-or-later

import "ol/ol.css?inline";
import { Feature, Map as OlMap, View } from "ol";
import { GeoJSON } from "ol/format";
import { Point } from "ol/geom";
import { Tile as TileLayer, Vector as VectorLayer } from "ol/layer";
import { fromLonLat } from "ol/proj";
import { OSM, Vector as VectorSource } from "ol/source";
import { Circle, Fill, Stroke, Style } from "ol/style";
import { Plugin } from "../Plugin.ts";

/**
 * MapView
 */
export default class MapView extends Plugin {
  private readonly map: HTMLElement;

  public constructor(map: HTMLElement) {
    super("mapView");

    this.map = map;
  }

  protected async run(): Promise<void> {
    const { leafletTarget: target, mapLon, mapLat, mapGeojson } = this.map.dataset;

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
  }

  protected async post(): Promise<void> {
    // noop
  }
}
