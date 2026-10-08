# ------------------------------------------------------------
# services/vehicle_pose.py
# Tractor Board - Gemeinsame Fahrzeugposition
# ------------------------------------------------------------

from dataclasses import dataclass
from time import time


@dataclass
class VehiclePose:

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

    # Aktuell verwendete Ausrichtung
    heading: float = 0.0

    # --------------------------------------------------------
    # GPS Qualität
    # --------------------------------------------------------

    gps_fix: bool = False
    gps_fix_type: str = "KEIN FIX"

    satellites: int = 0
    satellites_used: int = 0

    hdop: float = 99.99
    pdop: float = 99.99
    vdop: float = 99.99

    # --------------------------------------------------------
    # Zeit
    # --------------------------------------------------------

    timestamp: float = 0.0


class VehiclePoseService:

    def __init__(self):

        self.pose = VehiclePose(
            timestamp=time()
        )

    # ========================================================
    # GPS AKTUALISIEREN
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

        self.pose.latitude = latitude
        self.pose.longitude = longitude

        self.pose.speed = speed

        self.pose.gps_heading = heading

        self.pose.gps_fix = gps_fix
        self.pose.gps_fix_type = gps_fix_type

        self.pose.satellites = satellites
        self.pose.satellites_used = satellites_used

        self.pose.hdop = hdop
        self.pose.pdop = pdop
        self.pose.vdop = vdop

        self.pose.timestamp = time()

        # ----------------------------------------------------
        # GPS-Kurs zunächst als Ausrichtung verwenden,
        # wenn ein gültiger GPS-Fix vorhanden ist.
        # ----------------------------------------------------

        if gps_fix:

            self.pose.heading = heading

    # ========================================================
    # IMU AKTUALISIEREN
    # ========================================================

    def update_imu(
        self,
        heading
    ):

        self.pose.imu_heading = heading

        # ----------------------------------------------------
        # Für den Prototyp verwenden wir die IMU-Ausrichtung
        # als aktuelle Ausrichtung.
        #
        # Später kommt hier eine Fusion aus:
        #
        # GPS
        # IMU
        # Gyroskop
        # Magnetometer
        # ggf. RTK
        #
        # ----------------------------------------------------

        self.pose.heading = heading

        self.pose.timestamp = time()

    # ========================================================
    # POSITION ABFRAGEN
    # ========================================================

    def get_pose(self):

        return self.pose
