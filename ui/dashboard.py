# ------------------------------------------------------------
# ui/dashboard.py
# Tractor Board - Hauptanzeige
# ------------------------------------------------------------

from datetime import datetime

from kivy.clock import Clock
from kivy.metrics import dp

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

from ui.map_panel import TractorMap

from services.gps import GPSService
from services.vehicle import VehicleService


# ------------------------------------------------------------
# Farben
# ------------------------------------------------------------

BG_COLOR = (
    0.06,
    0.07,
    0.07,
    1
)

GREEN = (
    0.25,
    0.75,
    0.25,
    1
)

RED = (
    0.85,
    0.15,
    0.15,
    1
)

WHITE = (
    1,
    1,
    1,
    1
)

GRAY = (
    0.65,
    0.68,
    0.68,
    1
)


# ------------------------------------------------------------
# Hilfsfunktion für Labels
# ------------------------------------------------------------

def create_label(
    text="",
    font_size="20sp",
    color=WHITE,
    bold=False
):

    label = Label(
        text=text,
        font_size=font_size,
        color=color,
        bold=bold,
        halign="center",
        valign="middle"
    )


    label.bind(
        size=lambda instance, value:
        setattr(
            instance,
            "text_size",
            value
        )
    )


    return label


# ------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------

class TractorDashboard(BoxLayout):

    def __init__(
        self,
        app,
        **kwargs
    ):

        super().__init__(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(10),
            **kwargs
        )


        self.app = app


        # ----------------------------------------------------
        # Service-Status
        # ----------------------------------------------------

        self.services_running = False


        self.gps = None
        self.vehicle = None

        self.clock_event = None


        # ----------------------------------------------------
        # Benutzeroberfläche
        # ----------------------------------------------------

        self.build_ui()


        # ----------------------------------------------------
        # Services starten
        # ----------------------------------------------------

        self.start_services()


    # ========================================================
    # BENUTZEROBERFLÄCHE
    # ========================================================

    def build_ui(self):

        # ====================================================
        # HEADER
        # ====================================================

        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(65),
            spacing=dp(10)
        )


        # ----------------------------------------------------
        # Titel
        # ----------------------------------------------------

        title = create_label(
            text="TRACTOR BOARD",
            font_size="30sp",
            bold=True
        )

        title.size_hint_x = 0.35

        header.add_widget(title)


        # ----------------------------------------------------
        # GPS Status
        # ----------------------------------------------------

        self.gps_status = create_label(
            text="GPS ● WARTEN",
            font_size="19sp",
            color=GRAY,
            bold=True
        )

        self.gps_status.size_hint_x = 0.20

        header.add_widget(
            self.gps_status
        )


        # ----------------------------------------------------
        # Uhr
        # ----------------------------------------------------

        self.clock = create_label(
            text="--:--:--",
            font_size="25sp",
            bold=True
        )

        self.clock.size_hint_x = 0.20

        header.add_widget(
            self.clock
        )


        # ----------------------------------------------------
        # Fahrzeugstatus
        # ----------------------------------------------------

        self.vehicle_status = create_label(
            text="BETRIEB",
            font_size="20sp",
            color=GREEN,
            bold=True
        )

        self.vehicle_status.size_hint_x = 0.25

        header.add_widget(
            self.vehicle_status
        )


        self.add_widget(header)


        # ====================================================
        # HAUPTBEREICH
        # ====================================================

        content = BoxLayout(
            orientation="horizontal",
            spacing=dp(10)
        )


        # ====================================================
        # LINKES PANEL - FAHRZEUG
        # ====================================================

        left = BoxLayout(
            orientation="vertical",
            size_hint_x=0.22,
            padding=dp(10),
            spacing=dp(5)
        )


        left.add_widget(
            create_label(
                text="FAHRZEUG",
                font_size="22sp",
                bold=True
            )
        )


        left.add_widget(
            create_label(
                text="Geschwindigkeit",
                font_size="17sp"
            )
        )


        self.speed_label = create_label(
            text="0.0 km/h",
            font_size="38sp",
            color=GREEN,
            bold=True
        )

        left.add_widget(
            self.speed_label
        )


        left.add_widget(
            create_label(
                text="Motordrehzahl",
                font_size="17sp"
            )
        )


        self.rpm_label = create_label(
            text="0 rpm",
            font_size="30sp",
            bold=True
        )

        left.add_widget(
            self.rpm_label
        )


        left.add_widget(
            create_label(
                text="Kraftstoff",
                font_size="17sp"
            )
        )


        self.fuel_label = create_label(
            text="0 %",
            font_size="30sp",
            color=GREEN,
            bold=True
        )

        left.add_widget(
            self.fuel_label
        )


        left.add_widget(
            create_label(
                text="Kühlmittel",
                font_size="17sp"
            )
        )


        self.temperature_label = create_label(
            text="0 °C",
            font_size="30sp",
            bold=True
        )

        left.add_widget(
            self.temperature_label
        )


        content.add_widget(left)


        # ====================================================
        # MITTE - KARTE
        # ====================================================

        self.map_panel = TractorMap(
            size_hint_x=0.56
        )


        content.add_widget(
            self.map_panel
        )


        # ====================================================
        # RECHTES PANEL - ARBEIT
        # ====================================================

        right = BoxLayout(
            orientation="vertical",
            size_hint_x=0.22,
            padding=dp(10),
            spacing=dp(5)
        )


        right.add_widget(
            create_label(
                text="ARBEIT",
                font_size="22sp",
                bold=True
            )
        )


        right.add_widget(
            create_label(
                text="Arbeitsbreite",
                font_size="17sp"
            )
        )


        self.width_label = create_label(
            text="3.00 m",
            font_size="30sp",
            bold=True
        )

        right.add_widget(
            self.width_label
        )


        right.add_widget(
            create_label(
                text="Fläche",
                font_size="17sp"
            )
        )


        self.area_label = create_label(
            text="0.00 ha",
            font_size="30sp",
            color=GREEN,
            bold=True
        )

        right.add_widget(
            self.area_label
        )


        right.add_widget(
            create_label(
                text="Arbeitszeit",
                font_size="17sp"
            )
        )


        self.worktime_label = create_label(
            text="00:00:00",
            font_size="27sp",
            bold=True
        )

        right.add_widget(
            self.worktime_label
        )


        right.add_widget(
            create_label(
                text="Fahrtrichtung",
                font_size="17sp"
            )
        )


        self.heading_label = create_label(
            text="0°",
            font_size="30sp",
            bold=True
        )

        right.add_widget(
            self.heading_label
        )


        content.add_widget(right)


        self.add_widget(content)


        # ====================================================
        # FOOTER
        # ====================================================

        footer = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(75),
            spacing=dp(8)
        )


        # ----------------------------------------------------
        # MENÜ
        # ----------------------------------------------------

        menu_button = Button(
            text="MENÜ",
            font_size="20sp"
        )


        menu_button.bind(
            on_press=self.open_menu
        )


        footer.add_widget(
            menu_button
        )


        # ----------------------------------------------------
        # GPS
        # ----------------------------------------------------

        gps_button = Button(
            text="GPS",
            font_size="20sp"
        )


        footer.add_widget(
            gps_button
        )


        # ----------------------------------------------------
        # ARBEIT
        # ----------------------------------------------------

        work_button = Button(
            text="ARBEIT",
            font_size="20sp"
        )


        footer.add_widget(
            work_button
        )


        # ----------------------------------------------------
        # EINSTELLUNGEN
        # ----------------------------------------------------

        settings_button = Button(
            text="EINSTELLUNGEN",
            font_size="18sp"
        )


        footer.add_widget(
            settings_button
        )


        # ----------------------------------------------------
        # BEENDEN
        # ----------------------------------------------------

        exit_button = Button(
            text="BEENDEN",
            font_size="21sp",
            background_color=RED
        )


        exit_button.bind(
            on_release=self.app.close_app
        )


        footer.add_widget(
            exit_button
        )


        self.add_widget(footer)


    # ========================================================
    # MENÜ
    # ========================================================

    def open_menu(self, instance):
        print("MENÜ GEDRÜCKT", flush=True)
        self.app.show_machine_manager()


    # ========================================================
    # SERVICES STARTEN
    # ========================================================

    def start_services(self):

        if self.services_running:

            return


        # ----------------------------------------------------
        # GPS Service
        # ----------------------------------------------------

        if self.gps is None:

            self.gps = GPSService(
                callback=self.update_gps
            )


        self.gps.start()


        # ----------------------------------------------------
        # Fahrzeug Service
        # ----------------------------------------------------

        if self.vehicle is None:

            self.vehicle = VehicleService(
                callback=self.update_vehicle
            )


        self.vehicle.start()


        # ----------------------------------------------------
        # Uhr
        # ----------------------------------------------------

        if self.clock_event is None:

            self.clock_event = Clock.schedule_interval(
                self.update_clock,
                1.0
            )


        self.services_running = True


    # ========================================================
    # SERVICES STOPPEN
    # ========================================================

    def stop_services(self):

        if not self.services_running:

            return


        # ----------------------------------------------------
        # GPS
        # ----------------------------------------------------

        if self.gps is not None:

            self.gps.stop()


        # ----------------------------------------------------
        # Fahrzeug
        # ----------------------------------------------------

        if self.vehicle is not None:

            self.vehicle.stop()


        # ----------------------------------------------------
        # Uhr
        # ----------------------------------------------------

        if self.clock_event is not None:

            self.clock_event.cancel()

            self.clock_event = None


        self.services_running = False


    # ========================================================
    # GPS DATEN
    # ========================================================

    def update_gps(
        self,
        latitude,
        longitude,
        speed,
        heading
    ):

        self.speed_label.text = (
            f"{speed:.1f} km/h"
        )


        self.heading_label.text = (
            f"{heading:.0f}°"
        )


        self.gps_status.text = (
            "GPS ● AKTIV"
        )


        self.gps_status.color = GREEN


        # ----------------------------------------------------
        # Karte aktualisieren
        # ----------------------------------------------------

        if self.map_panel is not None:

            self.map_panel.update_position(
                latitude,
                longitude,
                speed,
                heading
            )


    # ========================================================
    # FAHRZEUGDATEN
    # ========================================================

    def update_vehicle(
        self,
        rpm,
        fuel,
        temperature
    ):

        self.rpm_label.text = (
            f"{rpm} rpm"
        )


        self.fuel_label.text = (
            f"{fuel} %"
        )


        self.temperature_label.text = (
            f"{temperature} °C"
        )


    # ========================================================
    # UHR
    # ========================================================

    def update_clock(self, dt):

        self.clock.text = (
            datetime.now().strftime(
                "%H:%M:%S"
            )
        )


    # ========================================================
    # AUFRÄUMEN
    # ========================================================

    def cleanup(self):

        self.stop_services()

