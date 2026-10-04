# ------------------------------------------------------------
# ui/map_panel.py
# ------------------------------------------------------------

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from kivy_garden.mapview import MapView
from kivy_garden.mapview import MapMarker

from config import (
    START_LATITUDE,
    START_LONGITUDE,
    MAP_ZOOM
)


class TractorMap(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(
            orientation="vertical",
            **kwargs
        )


        # ----------------------------------------------------
        # Karte
        # ----------------------------------------------------

        self.map = MapView(
            lat=START_LATITUDE,
            lon=START_LONGITUDE,
            zoom=MAP_ZOOM
        )

        self.add_widget(self.map)


        # ----------------------------------------------------
        # Fahrzeugmarker
        # ----------------------------------------------------

        self.marker = MapMarker(
            lat=START_LATITUDE,
            lon=START_LONGITUDE
        )

        self.map.add_widget(self.marker)


        # ----------------------------------------------------
        # GPS Status
        # ----------------------------------------------------

        self.status = Label(
            text="GPS: WARTEN",
            size_hint_y=None,
            height=35,
            font_size="18sp"
        )

        self.add_widget(self.status)


    def update_position(
            self,
            latitude,
            longitude,
            speed,
            heading
    ):

        # Marker bewegen
        self.marker.lat = latitude
        self.marker.lon = longitude


        # Karte auf Fahrzeug zentrieren
        self.map.center_on(
            latitude,
            longitude
        )


        # Status aktualisieren
        self.status.text = (
            f"GPS: AKTIV   "
            f"{speed:.1f} km/h   "
            f"{heading:.0f}°"
        )

