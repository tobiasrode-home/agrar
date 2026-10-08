# ------------------------------------------------------------
# services/navigation.py
# Tractor Board - Navigation Service
# ------------------------------------------------------------

import math
import time

from dataclasses import dataclass


# ------------------------------------------------------------
# Zustände
# ------------------------------------------------------------

STATE_IDLE = "IDLE"
STATE_WORKING = "WORKING"
STATE_PAUSED = "PAUSED"


# ------------------------------------------------------------
# Navigationsdaten
# ------------------------------------------------------------

@dataclass
class NavigationData:

    # --------------------------------------------------------
    # Position
    # --------------------------------------------------------

    latitude: float = 0.0
    longitude: float = 0.0

    # --------------------------------------------------------
    # Bewegung
    # --------------------------------------------------------

    speed: float = 0.0

    # --------------------------------------------------------
    # Ausrichtung
    # --------------------------------------------------------

    gps_heading: float = 0.0
    imu_heading: float = 0.0

    heading: float = 0.0

    # --------------------------------------------------------
    # GPS
    # --------------------------------------------------------

    gps_fix: bool = False
    gps_fix_type: str = "KEIN FIX"

    satellites: int = 0
    satellites_used: int = 0

    hdop: float = 99.99
    pdop: float = 99.99
    vdop: float = 99.99

    # --------------------------------------------------------
    # Bewegungsstatus
    # --------------------------------------------------------

    state: str = STATE_IDLE

    # --------------------------------------------------------
    # Zeit
    # --------------------------------------------------------

    timestamp: float = 0.0


# ------------------------------------------------------------
# Navigation Service
# ------------------------------------------------------------

class NavigationService:

    def __init__(
        self,
        callback=None
    ):

        self.callback = callback

        self.data = NavigationData(
            timestamp=time.time()
        )

        # ----------------------------------------------------
        # Sensorwerte
        # ----------------------------------------------------

        self.gps_available = False
        self.imu_available = False

        # ----------------------------------------------------
        # Schwellenwerte
        # ----------------------------------------------------

        # Unterhalb dieser Geschwindigkeit betrachten wir
        # den GPS-Kurs als unzuverlässig.
        #
        # Der NEO-6M kann im Stillstand keinen sinnvollen
        # Bewegungsvektor liefern.
        # ----------------------------------------------------

        self.gps_heading_min_speed = 0.5

        # km/h
        self.moving_speed_threshold = 0.2

        # ----------------------------------------------------
        # Arbeitszustand
        # ----------------------------------------------------

        self.state = STATE_IDLE

    # ========================================================
    # GPS DATEN
    # ========================================================

    def update_gps(
        self,
        latitude,
        longitude,
        speed,
        heading,
        gps_fix=False,
        gps_fix_type="KEIN FIX",
        satellites=0,
        satellites_used=0,
        hdop=99.99,
        pdop=99.99,
        vdop=99.99
    ):

        # ----------------------------------------------------
        # GPS verfügbar
        # ----------------------------------------------------

        self.gps_available = True

        # ----------------------------------------------------
        # Position
        # ----------------------------------------------------

        if latitude is not None:

            self.data.latitude = latitude

        if longitude is not None:

            self.data.longitude = longitude

        # ----------------------------------------------------
        # Geschwindigkeit
        # ----------------------------------------------------

        if speed is not None:

            self.data.speed = speed

        # ----------------------------------------------------
        # GPS Kurs
        # ----------------------------------------------------

        if heading is not None:

            self.data.gps_heading = (
                self.normalize_heading(
                    heading
                )
            )

        # ----------------------------------------------------
        # GPS Status
        # ----------------------------------------------------

        self.data.gps_fix = gps_fix

        self.data.gps_fix_type = (
            gps_fix_type
        )

        self.data.satellites = (
            satellites
        )

        self.data.satellites_used = (
            satellites_used
        )

        self.data.hdop = (
            hdop
        )

        self.data.pdop = (
            pdop
        )

        self.data.vdop = (
            vdop
        )

        # ----------------------------------------------------
        # Ausrichtung aktualisieren
        # ----------------------------------------------------

        self._update_heading()

        # ----------------------------------------------------
        # Zustand aktualisieren
        # ----------------------------------------------------

        self._update_motion_state()

        # ----------------------------------------------------
        # Zeit
        # ----------------------------------------------------

        self.data.timestamp = (
            time.time()
        )

        self._notify()

    # ========================================================
    # IMU DATEN
    # ========================================================

    def update_imu(
        self,
        heading
    ):

        self.imu_available = True

        if heading is not None:

            self.data.imu_heading = (
                self.normalize_heading(
                    heading
                )
            )

        # ----------------------------------------------------
        # Ausrichtung aktualisieren
        # ----------------------------------------------------

        self._update_heading()

        # ----------------------------------------------------
        # Zeit
        # ----------------------------------------------------

        self.data.timestamp = (
            time.time()
        )

        self._notify()

    # ========================================================
    # AUSRICHTUNG
    # ========================================================

    def _update_heading(self):

        speed = self.data.speed

        # ----------------------------------------------------
        # Während der Fahrt:
        #
        # GPS-Kurs verwenden, wenn GPS-Fix vorhanden ist.
        # ----------------------------------------------------

        if (
            self.data.gps_fix
            and speed >= self.gps_heading_min_speed
        ):

            self.data.heading = (
                self.data.gps_heading
            )

            return

        # ----------------------------------------------------
        # Im Stand:
        #
        # IMU verwenden.
        # ----------------------------------------------------

        if self.imu_available:

            self.data.heading = (
                self.data.imu_heading
            )

            return

        # ----------------------------------------------------
        # Falls keine IMU vorhanden ist,
        # letzten GPS-Kurs behalten.
        # ----------------------------------------------------

        if self.data.gps_fix:

            self.data.heading = (
                self.data.gps_heading
            )

    # ========================================================
    # BEWEGUNGSSTATUS
    # ========================================================

    def _update_motion_state(self):

        # ----------------------------------------------------
        # PAUSED bleibt bestehen.
        #
        # Die Bewegung des Traktors darf den Zustand nicht
        # automatisch wieder auf WORKING setzen.
        # ----------------------------------------------------

        if self.state == STATE_PAUSED:

            self.data.state = (
                STATE_PAUSED
            )

            return

        # ----------------------------------------------------
        # Geschwindigkeit prüfen
        # ----------------------------------------------------

        if (
            self.data.speed
            >= self.moving_speed_threshold
        ):

            self.data.state = (
                STATE_IDLE
            )

        else:

            self.data.state = (
                STATE_IDLE
            )

    # ========================================================
    # ARBEIT STARTEN
    # ========================================================

    def start_work(self):

        self.state = STATE_WORKING

        self.data.state = (
            STATE_WORKING
        )

        self.data.timestamp = (
            time.time()
        )

        self._notify()

    # ========================================================
    # ARBEIT PAUSIEREN
    # ========================================================

    def pause_work(self):

        self.state = STATE_PAUSED

        self.data.state = (
            STATE_PAUSED
        )

        self.data.timestamp = (
            time.time()
        )

        self._notify()

    # ========================================================
    # ARBEIT BEENDEN
    # ========================================================

    def stop_work(self):

        self.state = STATE_IDLE

        self.data.state = (
            STATE_IDLE
        )

        self.data.timestamp = (
            time.time()
        )

        self._notify()

    # ========================================================
    # STATUS ABFRAGEN
    # ========================================================

    def get_data(self):

        return self.data

    # ========================================================
    # CALLBACK
    # ========================================================

    def _notify(self):

        if self.callback is None:

            return

        try:

            self.callback(
                self.data
            )

        except Exception as error:

            print(
                f"Navigation Callback Fehler: {error}",
                flush=True
            )

    # ========================================================
    # KURS NORMALISIEREN
    # ========================================================

    @staticmethod
    def normalize_heading(
        heading
    ):

        if heading is None:

            return 0.0

        heading = float(
            heading
        )

        heading %= 360.0

        if heading < 0:

            heading += 360.0

        return heading

    # ========================================================
    # WINKELDIFFERENZ
    # ========================================================

    @staticmethod
    def heading_difference(
        target,
        current
    ):

        target = (
            NavigationService.normalize_heading(
                target
            )
        )

        current = (
            NavigationService.normalize_heading(
                current
            )
        )

        difference = (
            target - current
        )

        if difference > 180:

            difference -= 360

        elif difference < -180:

            difference += 360

        return difference

    # ========================================================
    # ENTFERNUNG ZWISCHEN GPS-PUNKTEN
    # ========================================================

    @staticmethod
    def distance_between(
        latitude1,
        longitude1,
        latitude2,
        longitude2
    ):

        # ----------------------------------------------------
        # Haversine
        #
        # Ergebnis in Metern
        # ----------------------------------------------------

        earth_radius = 6371000.0

        lat1 = math.radians(
            latitude1
        )

        lat2 = math.radians(
            latitude2
        )

        delta_lat = math.radians(
            latitude2 - latitude1
        )

        delta_lon = math.radians(
            longitude2 - longitude1
        )

        a = (
            math.sin(delta_lat / 2) ** 2
            +
            math.cos(lat1)
            *
            math.cos(lat2)
            *
            math.sin(delta_lon / 2) ** 2
        )

        c = (
            2
            *
            math.atan2(
                math.sqrt(a),
                math.sqrt(1 - a)
            )
        )

        return (
            earth_radius * c
        )

    # ========================================================
    # RICHTUNG ZWISCHEN GPS-PUNKTEN
    # ========================================================

    @staticmethod
    def bearing_between(
        latitude1,
        longitude1,
        latitude2,
        longitude2
    ):

        lat1 = math.radians(
            latitude1
        )

        lat2 = math.radians(
            latitude2
        )

        delta_lon = math.radians(
            longitude2 - longitude1
        )

        x = (
            math.sin(delta_lon)
            *
            math.cos(lat2)
        )

        y = (
            math.cos(lat1)
            *
            math.sin(lat2)
            -
            math.sin(lat1)
            *
            math.cos(lat2)
            *
            math.cos(delta_lon)
        )

        bearing = math.degrees(
            math.atan2(
                x,
                y
            )
        )

        return (
            NavigationService.normalize_heading(
                bearing
            )
        )
