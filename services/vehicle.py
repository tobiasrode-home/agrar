# ------------------------------------------------------------
# services/vehicle.py
# ------------------------------------------------------------

from kivy.clock import Clock


class VehicleService:

    def __init__(self, callback=None):

        self.callback = callback

        self.rpm = 1850
        self.fuel = 78
        self.temperature = 82

        self.running = False

        self._event = None


    def start(self):

        if self.running:
            return

        self.running = True

        self._event = Clock.schedule_interval(
            self._update,
            1.0
        )


    def stop(self):

        if self._event:
            self._event.cancel()

        self._event = None
        self.running = False


    def _update(self, dt):

        # ----------------------------------------------------
        # TESTDATEN
        # ----------------------------------------------------

        # Später:
        #
        # CAN-Bus
        # OBD
        # ISOBUS
        # Sensoren
        #

        self.rpm += 1

        if self.rpm > 1900:
            self.rpm = 1800


        if self.callback:

            self.callback(
                self.rpm,
                self.fuel,
                self.temperature
            )
