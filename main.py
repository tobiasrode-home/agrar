# ------------------------------------------------------------
# main.py
# Tractor Board Computer
# ------------------------------------------------------------

from kivy.config import Config

Config.set("graphics", "width", "1280")
Config.set("graphics", "height", "720")
Config.set("graphics", "resizable", "0")
Config.set("graphics", "rotation", "270")

from kivy.app import App
from kivy.core.window import Window

from database.database import Database
from ui.work_dashboard import WorkDashboard
from ui.machine_manager import MachineManager


BACKGROUND_COLOR = (
    0.06,
    0.07,
    0.07,
    1,
)


class TractorBoard(App):

    def build(self):
        print(
            "Tractor Board wird gestartet...",
            flush=True,
        )

        Window.clearcolor = BACKGROUND_COLOR

        print(
            "Initialisiere Datenbank...",
            flush=True,
        )

        self.database = Database()

        self.dashboard = None
        self.machine_manager = None

        self.dashboard = WorkDashboard(app=self)

        print(
            "Dashboard bereit.",
            flush=True,
        )

        return self.dashboard

    # --------------------------------------------------------
    # DASHBOARD ANZEIGEN
    # --------------------------------------------------------

    def show_dashboard(self):
        print(
            "Öffne Dashboard...",
            flush=True,
        )

        if self.machine_manager is not None:
            try:
                if self.machine_manager.parent is not None:
                    Window.remove_widget(self.machine_manager)
            except Exception as error:
                print(
                    f"Fehler beim Entfernen der "
                    f"Maschinenverwaltung: {error}",
                    flush=True,
                )

            self.machine_manager = None

        if self.dashboard is None:
            self.dashboard = WorkDashboard(app=self)

        if self.dashboard.parent is None:
            Window.add_widget(self.dashboard)

        self.root = self.dashboard
        self.dashboard.start_services()

        print(
            "Dashboard angezeigt.",
            flush=True,
        )

    # --------------------------------------------------------
    # MASCHINENVERWALTUNG ANZEIGEN
    # --------------------------------------------------------

    def show_machine_manager(self):
        print(
            "Öffne Maschinenverwaltung...",
            flush=True,
        )

        if self.dashboard is not None:
            self.dashboard.stop_services()

            if self.dashboard.parent is not None:
                Window.remove_widget(self.dashboard)

        if self.machine_manager is not None:
            if self.machine_manager.parent is not None:
                Window.remove_widget(self.machine_manager)

        self.machine_manager = MachineManager(
            app=self,
            database=self.database,
        )

        Window.add_widget(self.machine_manager)
        self.root = self.machine_manager

        print(
            "Maschinenverwaltung angezeigt.",
            flush=True,
        )

    # --------------------------------------------------------
    # ANWENDUNG SCHLIESSEN
    # --------------------------------------------------------

    def close_app(self, instance=None):
        print(
            "Tractor Board wird beendet...",
            flush=True,
        )

        if self.dashboard is not None:
            self.dashboard.stop_services()

        if self.database is not None:
            self.database.close()

        self.stop()

    def on_stop(self):
        """
        Kivy ruft on_stop auch beim regulären Beenden auf.
        Die Datenbankverbindung wird in close_app geschlossen.
        """
        pass


if __name__ == "__main__":
    TractorBoard().run()
