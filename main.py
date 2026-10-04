# ------------------------------------------------------------
# main.py
# Tractor Board Computer
# ------------------------------------------------------------

from kivy.config import Config


# ------------------------------------------------------------
# Display-Einstellungen
# ------------------------------------------------------------

Config.set(
    "graphics",
    "width",
    "1280"
)

Config.set(
    "graphics",
    "height",
    "720"
)

Config.set(
    "graphics",
    "resizable",
    "0"
)

# Rotation bei Bedarf aktivieren
Config.set(
    "graphics",
    "rotation",
    "270"
)


# ------------------------------------------------------------
# Kivy
# ------------------------------------------------------------

from kivy.app import App
from kivy.core.window import Window


# ------------------------------------------------------------
# Eigene Module
# ------------------------------------------------------------

from database.database import Database

from ui.dashboard import TractorDashboard
from ui.machine_manager import MachineManager


# ------------------------------------------------------------
# Farben
# ------------------------------------------------------------

BACKGROUND_COLOR = (
    0.06,
    0.07,
    0.07,
    1
)


# ------------------------------------------------------------
# Tractor Board
# ------------------------------------------------------------

class TractorBoard(App):

    # ========================================================
    # APPLICATION START
    # ========================================================

    def build(self):

        print(
            "Tractor Board wird gestartet...",
            flush=True
        )

        # ----------------------------------------------------
        # Fenster
        # ----------------------------------------------------

        Window.clearcolor = BACKGROUND_COLOR


        # ----------------------------------------------------
        # Datenbank
        # ----------------------------------------------------

        print(
            "Initialisiere Datenbank...",
            flush=True
        )

        self.database = Database()


        # ----------------------------------------------------
        # Ansichten
        # ----------------------------------------------------

        self.dashboard = None

        self.machine_manager = None


        # ----------------------------------------------------
        # Dashboard erzeugen
        # ----------------------------------------------------

        print(
            "Erzeuge Dashboard...",
            flush=True
        )

        self.dashboard = TractorDashboard(
            app=self
        )


        print(
            "Dashboard bereit.",
            flush=True
        )


        # ----------------------------------------------------
        # Dashboard zurückgeben
        # ----------------------------------------------------

        return self.dashboard


    # ========================================================
    # DASHBOARD
    # ========================================================

    def show_dashboard(self):

        print(
            "Öffne Dashboard...",
            flush=True
        )


        # ----------------------------------------------------
        # Maschinenverwaltung entfernen
        # ----------------------------------------------------

        if self.machine_manager is not None:

            print(
                "Entferne Maschinenverwaltung...",
                flush=True
            )

            try:

                Window.remove_widget(
                    self.machine_manager
                )

            except Exception as error:

                print(
                    f"Fehler beim Entfernen der "
                    f"Maschinenverwaltung: {error}",
                    flush=True
                )


            self.machine_manager = None


        # ----------------------------------------------------
        # Dashboard anzeigen
        # ----------------------------------------------------

        if self.dashboard is None:

            print(
                "Dashboard existiert noch nicht - "
                "erzeuge neues Dashboard.",
                flush=True
            )

            self.dashboard = TractorDashboard(
                app=self
            )


        # ----------------------------------------------------
        # Prüfen, ob Dashboard bereits angezeigt wird
        # ----------------------------------------------------

        if self.dashboard.parent is None:

            Window.add_widget(
                self.dashboard
            )


        # ----------------------------------------------------
        # Root setzen
        # ----------------------------------------------------

        self.root = self.dashboard


        # ----------------------------------------------------
        # Services starten
        # ----------------------------------------------------

        self.dashboard.start_services()


        print(
            "Dashboard angezeigt.",
            flush=True
        )


    # ========================================================
    # MASCHINENVERWALTUNG
    # ========================================================

    def show_machine_manager(self):

        print(
            "Öffne Maschinenverwaltung...",
            flush=True
        )


        # ----------------------------------------------------
        # Dashboard-Services stoppen
        # ----------------------------------------------------

        if self.dashboard is not None:

            print(
                "Stoppe Dashboard-Services...",
                flush=True
            )

            self.dashboard.stop_services()


        # ----------------------------------------------------
        # Dashboard entfernen
        # ----------------------------------------------------

        if self.dashboard is not None:

            if self.dashboard.parent is not None:

                print(
                    "Entferne Dashboard aus Window...",
                    flush=True
                )

                Window.remove_widget(
                    self.dashboard
                )


        # ----------------------------------------------------
        # Alte Maschinenverwaltung entfernen
        # ----------------------------------------------------

        if self.machine_manager is not None:

            if self.machine_manager.parent is not None:

                Window.remove_widget(
                    self.machine_manager
                )


        # ----------------------------------------------------
        # Maschinenverwaltung erzeugen
        # ----------------------------------------------------

        print(
            "Erzeuge MachineManager...",
            flush=True
        )

        self.machine_manager = MachineManager(
            app=self,
            database=self.database
        )


        # ----------------------------------------------------
        # Maschinenverwaltung anzeigen
        # ----------------------------------------------------

        Window.add_widget(
            self.machine_manager
        )


        # ----------------------------------------------------
        # Root aktualisieren
        # ----------------------------------------------------

        self.root = self.machine_manager


        print(
            "Maschinenverwaltung angezeigt.",
            flush=True
        )


    # ========================================================
    # ANWENDUNG BEENDEN
    # ========================================================

    def close_app(self, instance=None):

        print(
            "Tractor Board wird beendet...",
            flush=True
        )


        # ----------------------------------------------------
        # Dashboard-Services stoppen
        # ----------------------------------------------------

        if self.dashboard is not None:

            print(
                "Stoppe Dashboard-Services...",
                flush=True
            )

            self.dashboard.stop_services()


        # ----------------------------------------------------
        # Datenbank schließen
        # ----------------------------------------------------

        if self.database is not None:

            print(
                "Schließe Datenbank...",
                flush=True
            )

            self.database.close()


        # ----------------------------------------------------
        # Kivy beenden
        # ----------------------------------------------------

        print(
            "Beende Kivy...",
            flush=True
        )

        self.stop()


# ------------------------------------------------------------
# Programmstart
# ------------------------------------------------------------

if __name__ == "__main__":

    TractorBoard().run()

