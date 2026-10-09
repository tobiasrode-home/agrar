# ------------------------------------------------------------
# ui/map_panel.py
# Tractor Board - Kartenanzeige
# ------------------------------------------------------------

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from kivy_garden.mapview import (
    MapView,
    MapMarker,
    MapPolygon,
    MapPolyline,
)

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

        self.status.text = (
            f"GPS: AKTIV   "
            f"{speed:.1f} km/h   "
            f"{heading:.0f}°"
        )

    # --------------------------------------------------------
    # GPS-SPUR ZEICHNEN
    # --------------------------------------------------------

    def add_track_segment(self, coordinates):
        """
        coordinates:
            [[latitude, longitude], [latitude, longitude]]
        """
        if not coordinates or len(coordinates) < 2:
            return

        points = [
            (float(lat), float(lon))
            for lat, lon in coordinates
        ]

        line = MapPolyline(
            points=points,
            color=(0.15, 0.55, 0.95, 0.95),
            width=2.0,
        )

        self.map.add_widget(line)
        self.track_segments.append(line)

    # --------------------------------------------------------
    # BEARBEITETE FLÄCHE ZEICHNEN
    # --------------------------------------------------------

    def add_coverage_polygon(self, coordinates):
        """
        coordinates:
            [[latitude, longitude], ...]
        """
        if not coordinates or len(coordinates) < 3:
            return

        polygon = MapPolygon(
            coords=[
                (float(lat), float(lon))
                for lat, lon in coordinates
            ],
            color=(0.15, 0.65, 0.20, 0.35),
            line_color=(0.10, 0.45, 0.15, 0.9),
            line_width=1.0,
        )

        self.map.add_widget(polygon)
        self.coverage_polygons.append(polygon)

    # --------------------------------------------------------
    # ABDECKUNG ENTFERNEN
    # --------------------------------------------------------

    def clear_coverage_polygons(self):
        for polygon in self.coverage_polygons:
            if polygon.parent is self.map:
                self.map.remove_widget(polygon)

        self.coverage_polygons.clear()

    # --------------------------------------------------------
    # GPS-SPUR ENTFERNEN
    # --------------------------------------------------------

    def clear_track_segments(self):
        for segment in self.track_segments:
            if segment.parent is self.map:
                self.map.remove_widget(segment)

        self.track_segments.clear()
