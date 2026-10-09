# ------------------------------------------------------------
# ui/map_panel.py
# Tractor Board - Kartenanzeige
# ------------------------------------------------------------

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from kivy_garden.mapview import MapView, MapMarker
from kivy_garden.mapview.geojson import GeoJsonMapLayer

from config import (
    START_LATITUDE,
    START_LONGITUDE,
    MAP_ZOOM,
)


class TractorMap(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            **kwargs
        )

        self.has_position = False
        self.last_latitude = None
        self.last_longitude = None

        # Zeichnungsebenen für GPS-Spur und Arbeitsfläche.
        self.track_segments = []
        self.coverage_polygons = []

        self.map = MapView(
            lat=START_LATITUDE,
            lon=START_LONGITUDE,
            zoom=MAP_ZOOM,
        )

        self.add_widget(self.map)

        self.marker = MapMarker(
            lat=START_LATITUDE,
            lon=START_LONGITUDE,
        )

        self.map.add_widget(self.marker)

        self.status = Label(
            text="GPS: WARTEN",
            size_hint_y=None,
            height=35,
            font_size="18sp",
        )

        self.add_widget(self.status)

    # --------------------------------------------------------
    # GPS-POSITION AKTUALISIEREN
    # --------------------------------------------------------

    def update_position(
        self,
        latitude,
        longitude,
        speed,
        heading,
    ):
        if latitude is None or longitude is None:
            return

        latitude = float(latitude)
        longitude = float(longitude)

        if not (
            -90.0 <= latitude <= 90.0
            and -180.0 <= longitude <= 180.0
        ):
            return

        if latitude == 0.0 and longitude == 0.0:
            return

        self.last_latitude = latitude
        self.last_longitude = longitude

        self.marker.lat = latitude
        self.marker.lon = longitude

        if not self.has_position:
            self.map.center_on(latitude, longitude)
            self.has_position = True

        speed_value = (
            float(speed)
            if speed is not None
            else 0.0
        )

        heading_value = (
            float(heading)
            if heading is not None
            else 0.0
        )

        self.status.text = (
            f"GPS: AKTIV   "
            f"{speed_value:.1f} km/h   "
            f"{heading_value:.0f}°"
        )

    # --------------------------------------------------------
    # GEOJSON-LAYER ERSTELLEN
    # --------------------------------------------------------

    def _add_geojson_layer(self, geometry):
        """
        Erstellt eine MapView-Ebene aus einer GeoJSON-Geometrie.

        Unterstützt die von MapView dokumentierten Geometrien
        LineString und Polygon.
        """

        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {},
                }
            ],
        }

        layer = GeoJsonMapLayer(
            geojson=geojson,
        )

        self.map.add_widget(layer)

        return layer

    # --------------------------------------------------------
    # GPS-SPUR ZEICHNEN
    # --------------------------------------------------------

    def add_track_segment(self, coordinates):
        """
        Zeichnet ein GPS-Spursegment.

        coordinates:
            [
                [latitude, longitude],
                [latitude, longitude]
            ]
        """

        if not coordinates or len(coordinates) < 2:
            return

        points = []

        for lat, lon in coordinates:
            lat = float(lat)
            lon = float(lon)

            if not (
                -90.0 <= lat <= 90.0
                and -180.0 <= lon <= 180.0
            ):
                return

            # GeoJSON verwendet [longitude, latitude].
            points.append([lon, lat])

        geometry = {
            "type": "LineString",
            "coordinates": points,
        }

        layer = self._add_geojson_layer(geometry)
        self.track_segments.append(layer)

    # --------------------------------------------------------
    # BEARBEITETE FLÄCHE ZEICHNEN
    # --------------------------------------------------------

    def add_coverage_polygon(self, coordinates):
        """
        Zeichnet eine bearbeitete Fläche.

        coordinates:
            [
                [latitude, longitude],
                [latitude, longitude],
                [latitude, longitude],
                ...
            ]

        Die Koordinaten müssen mindestens drei unterschiedliche
        Eckpunkte enthalten.
        """

        if not coordinates or len(coordinates) < 3:
            return

        ring = []

        for lat, lon in coordinates:
            lat = float(lat)
            lon = float(lon)

            if not (
                -90.0 <= lat <= 90.0
                and -180.0 <= lon <= 180.0
            ):
                return

            # GeoJSON verwendet [longitude, latitude].
            ring.append([lon, lat])

        # Ein GeoJSON-Polygonring muss geschlossen sein.
        if ring[0] != ring[-1]:
            ring.append(ring[0])

        geometry = {
            "type": "Polygon",
            "coordinates": [ring],
        }

        layer = self._add_geojson_layer(geometry)
        self.coverage_polygons.append(layer)

    # --------------------------------------------------------
    # BEARBEITETE FLÄCHEN ENTFERNEN
    # --------------------------------------------------------

    def clear_coverage_polygons(self):
        """Entfernt alle auf der Karte gezeichneten Arbeitsflächen."""

        for layer in self.coverage_polygons[:]:
            if layer.parent is self.map:
                self.map.remove_widget(layer)

        self.coverage_polygons.clear()

    # --------------------------------------------------------
    # GPS-SPUR ENTFERNEN
    # --------------------------------------------------------

    def clear_track_segments(self):
        """Entfernt alle gezeichneten GPS-Spursegmente."""

        for layer in self.track_segments[:]:
            if layer.parent is self.map:
                self.map.remove_widget(layer)

        self.track_segments.clear()
