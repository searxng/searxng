import { searxng } from "./00_toolkit.ts";

searxng.ready(
  () => {
    searxng.listen("click", ".searxng_init_map", async function (this: HTMLElement, event: Event) {
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
      import("ol/ol.css");

      const { leafletTarget: target, mapLon, mapLat, mapGeojson } = this.dataset;

      const lon = parseFloat(mapLon || "0");
      const lat = parseFloat(mapLat || "0");
      const view = new View({ maxZoom: 16, enableRotation: false });
      const map = new OlMap({
        target,
        layers: [new TileLayer({ source: new OSM({ maxZoom: 16 }) })],
        view
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
  },
  { on: [searxng.endpoint === "results"] }
);
