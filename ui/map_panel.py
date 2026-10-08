# ------------------------------------------------------------
# ui/map_panel.py
# Tractor Board - Kartenanzeige
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


# ------------------------------------------------------------
# Tractor Map
# ------------------------------------------------------------

class TractorMap(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(
            orientation="vertical",
            **kwargs
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self.has_position = False

        self.last_latitude = None
        self.last_longitude = None

        # ----------------------------------------------------
        # Karte
        # ----------------------------------------------------

        self.map = MapView(
            lat=START_LATITUDE,
            lon=START_LONGITUDE,
            zoom=MAP_ZOOM
        )

        self.add_widget(
            self.map
        )

        # ----------------------------------------------------
        # Fahrzeugmarker
        # ----------------------------------------------------

        self.marker = MapMarker(
            lat=START_LATITUDE,
            lon=START_LONGITUDE
        )

        self.map.add_widget(
            self.marker
        )

        # ----------------------------------------------------
        # GPS Status
        # ----------------------------------------------------

        self.status = Label(
            text="GPS: WARTEN",
            size_hint_y=None,
            height=35,
            font_size="18sp"
        )

        self.add_widget(
            self.status
        )


    # ========================================================
    # POSITION AKTUALISIEREN
    # ========================================================

    def update_position(
        self,
        latitude,
        longitude,
        speed,
        heading
    ):

        # ----------------------------------------------------
        # Ungültige Werte ignorieren
        # ----------------------------------------------------

        if latitude is None:
            return

        if longitude is None:
            return

        if latitude == 0.0 and longitude == 0.0:
            return

        if not (
            -90.0 <= latitude <= 90.0
        ):
            return

        if not (
            -180.0 <= longitude <= 180.0
        ):
            return

        # ----------------------------------------------------
        # Position speichern
        # ----------------------------------------------------

        self.last_latitude = latitude
        self.last_longitude = longitude

        # ----------------------------------------------------
        # Fahrzeugmarker bewegen
        # ----------------------------------------------------

        self.marker.lat = latitude
        self.marker.lon = longitude

        # ----------------------------------------------------
        # Beim ersten gültigen GPS-Fix
        # Karte auf Fahrzeug zentrieren
        # ----------------------------------------------------

        if not self.has_position:

            self.map.center_on(
                latitude,
                longitude
            )

            self.has_position = True

        # ----------------------------------------------------
        # GPS Status
        # ----------------------------------------------------

        self.status.text = (
            f"GPS: AKTIV   "
            f"{speed:.1f} km/h   "
            f"{heading:.0f}°"
        )
