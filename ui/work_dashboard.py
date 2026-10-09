# ------------------------------------------------------------
# ui/work_dashboard.py
# Erweiterung des vorhandenen TractorDashboard
# ------------------------------------------------------------

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from config import (
    GPS_TO_HITCH_M,
    IMPLEMENT_HITCH_TO_EDGE_M,
    IMPLEMENT_MOUNT_POSITION,
    IMPLEMENT_WORKING_WIDTH_M,
    IMPLEMENT_NAME,
)

from services.work_session import WorkSessionService
from ui.dashboard import TractorDashboard


class WorkDashboard(TractorDashboard):

    def __init__(self, app, **kwargs):
        self.work_session = WorkSessionService(app.database)
        self.work_status_label = None
        self.work_button = None
        self.finish_button = None

        super().__init__(app=app, **kwargs)

    # --------------------------------------------------------
    # BENUTZEROBERFLÄCHE ERWEITERN
    # --------------------------------------------------------

    def build_ui(self):
        super().build_ui()

        # Im bestehenden Dashboard ist der Footer ein direktes
        # horizontales BoxLayout mit dem MENÜ-Button.
        footer = None

        for widget in self.children:
            if not isinstance(widget, BoxLayout):
                continue

            if any(
                isinstance(child, Button)
                and child.text == "MENÜ"
                for child in widget.children
            ):
                footer = widget
                break

        if footer is None:
            raise RuntimeError(
                "Dashboard-Footer mit MENÜ-Button nicht gefunden."
            )

        # Vorhandenen ARBEIT-Button wiederverwenden.
        for child in footer.children:
            if (
                isinstance(child, Button)
                and child.text == "ARBEIT"
            ):
                self.work_button = child
                break

        if self.work_button is None:
            raise RuntimeError(
                "Der vorhandene ARBEIT-Button wurde nicht gefunden."
            )

        self.work_button.text = "ARBEIT STARTEN"
        self.work_button.bind(
            on_release=self.toggle_work_session
        )

        self.finish_button = Button(
            text="ARBEIT BEENDEN",
            font_size="18sp",
            background_color=(0.75, 0.15, 0.15, 1),
            disabled=True,
        )

        self.finish_button.bind(
            on_release=self.finish_work_session
        )

        footer.add_widget(self.finish_button)

        self.work_status_label = self.create_work_status_label()
        footer.add_widget(self.work_status_label)

        self.refresh_work_buttons()

        # Bereits gespeicherte Abdeckung eines offenen
        # Arbeitsgangs erneut auf der Karte darstellen.
        session_id = self.work_session.get_open_session_id()

        if session_id is not None:
            polygons = self.work_session.get_session_polygons(
                session_id
            )

            for polygon in polygons:
                self.map_panel.add_coverage_polygon(polygon)

    def create_work_status_label(self):
        from kivy.uix.label import Label

        return Label(
            text="Arbeit: bereit",
            font_size="15sp",
            size_hint_x=0.8,
        )

    # --------------------------------------------------------
    # BUTTON-ZUSTAND
    # --------------------------------------------------------

    def refresh_work_buttons(self):
        state = self.work_session.status

        if state == "active":
            self.work_button.text = "ARBEIT PAUSIEREN"
            self.work_button.background_color = (
                0.85, 0.55, 0.10, 1
            )
            self.finish_button.disabled = False
            self.work_status_label.text = "Arbeit: AKTIV"

        elif state == "paused":
            self.work_button.text = "ARBEIT FORTSETZEN"
            self.work_button.background_color = (
                0.20, 0.60, 0.20, 1
            )
            self.finish_button.disabled = False
            self.work_status_label.text = "Arbeit: PAUSIERT"

        else:
            self.work_button.text = "ARBEIT STARTEN"
            self.work_button.background_color = (
                0.20, 0.60, 0.20, 1
            )
            self.finish_button.disabled = True
            self.work_status_label.text = "Arbeit: bereit"

    # --------------------------------------------------------
    # ARBEITSGANG START / PAUSE / FORTSETZEN
    # --------------------------------------------------------

    def toggle_work_session(self, instance):
        try:
            state = self.work_session.status

            if state == "idle":
                self.work_session.start(
                    implement_name=IMPLEMENT_NAME,
                    gps_to_hitch_m=GPS_TO_HITCH_M,
                    hitch_to_edge_m=IMPLEMENT_HITCH_TO_EDGE_M,
                    mount_position=IMPLEMENT_MOUNT_POSITION,
                    working_width_m=IMPLEMENT_WORKING_WIDTH_M,
                )

            elif state == "active":
                self.work_session.pause()

            elif state == "paused":
                self.work_session.resume()

            self.refresh_work_buttons()

        except (ValueError, RuntimeError) as error:
            print(
                f"Arbeitsgang nicht ausgeführt: {error}",
                flush=True,
            )

    def finish_work_session(self, instance):
        self.work_session.finish()
        self.refresh_work_buttons()

        print(
            "Arbeitsgang beendet und gespeichert.",
            flush=True,
        )

    # --------------------------------------------------------
    # GPS CALLBACK AUS DEM GPS-SERVICE
    # --------------------------------------------------------

    def update_gps(
        self,
        latitude,
        longitude,
        speed,
        heading,
    ):
        # GPSService kann aus einem Hintergrundthread melden.
        # UI- und SQLite-Zugriffe erfolgen deshalb im Kivy-Thread.
        Clock.schedule_once(
            lambda dt: self._handle_gps_fix(
                latitude,
                longitude,
                speed,
                heading,
            ),
            0,
        )

    def _handle_gps_fix(
        self,
        latitude,
        longitude,
        speed,
        heading,
    ):
        # Vorhandene Dashboard-Anzeige aktualisieren.
        super().update_gps(
            latitude,
            longitude,
            speed,
            heading,
        )

        result = self.work_session.process_fix(
            latitude=latitude,
            longitude=longitude,
            speed_kmh=speed,
            heading_deg=heading,
        )

        track_segment = result.get("track_segment")

        if track_segment is not None:
            self.map_panel.add_track_segment(track_segment)

        polygon = result.get("coverage_polygon")

        if polygon is not None:
            self.map_panel.add_coverage_polygon(polygon)
