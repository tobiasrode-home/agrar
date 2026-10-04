# ------------------------------------------------------------
# services/gps.py
# ------------------------------------------------------------

from kivy.clock import Clock

from config import (
    START_LATITUDE,
    START_LONGITUDE,
    GPS_UPDATE_INTERVAL
)


class GPSService:

    def __init__(self, callback=None):

        self.callback = callback

        self.latitude = START_LATITUDE
        self.longitude = START_LONGITUDE

        self.speed = 0.0
        self.heading = 0.0

        self.running = False

        self._event = None


    def start(self):

        if self.running:
            return

        self.running = True

        self._event = Clock.schedule_interval(
            self._update,
            GPS_UPDATE_INTERVAL
        )


    def stop(self):

        if self._event:
            self._event.cancel()

        self._event = None
        self.running = False


    def _update(self, dt):

        # ----------------------------------------------------
        # TEST-GPS
        # ----------------------------------------------------
        #
        # Hier simulieren wir momentan eine langsame Fahrt.
        #
        # Später kommt hier z.B.:
        #
        #   GPS-Empfänger
        #   /dev/serial0
        #   NMEA
        #   GPSD
        #
        # ----------------------------------------------------

        self.speed = 5.0

        # ungefähr 1 m Bewegung
        self.longitude += 0.00001

        self.heading = 90.0


        # ----------------------------------------------------
        # Daten an Oberfläche übergeben
        # ----------------------------------------------------

        if self.callback:

            self.callback(
                self.latitude,
                self.longitude,
                self.speed,
                self.heading
            )

