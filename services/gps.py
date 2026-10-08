# ------------------------------------------------------------
# services/gps.py
# Tractor Board - GPS Service
# ------------------------------------------------------------

import threading
import time

import serial


# ------------------------------------------------------------
# Einstellungen
# ------------------------------------------------------------

GPS_PORT = "/dev/ttyAMA0"
GPS_BAUDRATE = 9600
GPS_READ_TIMEOUT = 1.0


# ------------------------------------------------------------
# GPS Service
# ------------------------------------------------------------

class GPSService:

    def __init__(self, callback=None):

        self.callback = callback

        # ----------------------------------------------------
        # Position
        # ----------------------------------------------------

        self.latitude = 0.0
        self.longitude = 0.0

        # ----------------------------------------------------
        # Bewegung
        # ----------------------------------------------------

        self.speed = 0.0
        self.heading = 0.0

        # ----------------------------------------------------
        # GPS Status
        # ----------------------------------------------------

        self.fix = False

        # 0 = kein Fix
        # 1 = GPS / 2D
        # 2 = DGPS
        self.fix_type = 0

        self.fix_type_text = "KEIN FIX"

        # ----------------------------------------------------
        # Satelliten
        # ----------------------------------------------------

        self.satellites = 0

        # Satelliten, die aktuell für die
        # Positionsberechnung verwendet werden
        self.satellites_used = 0

        # ----------------------------------------------------
        # Genauigkeit
        # ----------------------------------------------------

        self.hdop = 99.99
        self.vdop = 99.99
        self.pdop = 99.99

        # ----------------------------------------------------
        # GPS Zeit
        # ----------------------------------------------------

        self.timestamp = None

        # ----------------------------------------------------
        # GSV Informationen
        # ----------------------------------------------------

        self.satellite_info = []

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self.running = False

        self.serial_connection = None
        self.thread = None

    # ========================================================
    # START
    # ========================================================

    def start(self):

        if self.running:
            return

        print(
            "GPS Service wird gestartet...",
            flush=True
        )

        # ----------------------------------------------------
        # Serielle Schnittstelle öffnen
        # ----------------------------------------------------

        try:

            self.serial_connection = serial.Serial(
                port=GPS_PORT,
                baudrate=GPS_BAUDRATE,
                timeout=GPS_READ_TIMEOUT
            )

        except Exception as error:

            print(
                f"GPS konnte nicht geöffnet werden: {error}",
                flush=True
            )

            self.serial_connection = None

            return

        self.running = True

        print(
            f"GPS verbunden: "
            f"{GPS_PORT} @ {GPS_BAUDRATE} Baud",
            flush=True
        )

        # ----------------------------------------------------
        # Hintergrundthread
        # ----------------------------------------------------

        self.thread = threading.Thread(
            target=self._read_loop,
            daemon=True
        )

        self.thread.start()

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        if not self.running:
            return

        print(
            "GPS Service wird gestoppt...",
            flush=True
        )

        self.running = False

        # ----------------------------------------------------
        # Serielle Verbindung schließen
        # ----------------------------------------------------

        if self.serial_connection is not None:

            try:

                self.serial_connection.close()

            except Exception:

                pass

            self.serial_connection = None

        # ----------------------------------------------------
        # Thread beenden
        # ----------------------------------------------------

        if self.thread is not None:

            self.thread.join(
                timeout=2.0
            )

            self.thread = None

        print(
            "GPS Service gestoppt.",
            flush=True
        )

    # ========================================================
    # GPS LESESCHLEIFE
    # ========================================================

    def _read_loop(self):

        print(
            "GPS Datenempfang gestartet.",
            flush=True
        )

        while self.running:

            try:

                line = self.serial_connection.readline()

                if not line:
                    continue

                sentence = line.decode(
                    "ascii",
                    errors="ignore"
                ).strip()

                if not sentence:
                    continue

                # ------------------------------------------------
                # Debug-Ausgabe
                # ------------------------------------------------

                print(
                    f"GPS: {sentence}",
                    flush=True
                )

                # ------------------------------------------------
                # NMEA verarbeiten
                # ------------------------------------------------

                self._parse_sentence(
                    sentence
                )

            except Exception as error:

                if self.running:

                    print(
                        f"GPS Lesefehler: {error}",
                        flush=True
                    )

                time.sleep(1)

        print(
            "GPS Datenempfang beendet.",
            flush=True
        )

    # ========================================================
    # NMEA SATZ VERARBEITEN
    # ========================================================

    def _parse_sentence(
        self,
        sentence
    ):

        # ----------------------------------------------------
        # GGA
        #
        # Position
        # Fix
        # Satelliten
        # HDOP
        # ----------------------------------------------------

        if (
            sentence.startswith("$GPGGA")
            or sentence.startswith("$GNGGA")
        ):

            self._parse_gga(
                sentence
            )

        # ----------------------------------------------------
        # GSA
        #
        # Fix-Typ
        # verwendete Satelliten
        # PDOP
        # HDOP
        # VDOP
        # ----------------------------------------------------

        elif (
            sentence.startswith("$GPGSA")
            or sentence.startswith("$GNGSA")
        ):

            self._parse_gsa(
                sentence
            )

        # ----------------------------------------------------
        # GSV
        #
        # sichtbare Satelliten
        # Signalstärke
        # ----------------------------------------------------

        elif (
            sentence.startswith("$GPGSV")
            or sentence.startswith("$GNGSV")
        ):

            self._parse_gsv(
                sentence
            )

        # ----------------------------------------------------
        # RMC
        #
        # Position
        # Geschwindigkeit
        # Kurs
        # Zeit
        # ----------------------------------------------------

        elif (
            sentence.startswith("$GPRMC")
            or sentence.startswith("$GNRMC")
        ):

            self._parse_rmc(
                sentence
            )

    # ========================================================
    # GGA
    # ========================================================

    def _parse_gga(
        self,
        sentence
    ):

        try:

            parts = sentence.split(",")

            if len(parts) < 9:
                return

            # ------------------------------------------------
            # UTC Zeit
            # ------------------------------------------------

            self.timestamp = parts[1]

            # ------------------------------------------------
            # Latitude
            # ------------------------------------------------

            latitude = parts[2]
            latitude_direction = parts[3]

            # ------------------------------------------------
            # Longitude
            # ------------------------------------------------

            longitude = parts[4]
            longitude_direction = parts[5]

            # ------------------------------------------------
            # Fix Qualität
            #
            # 0 = kein Fix
            # 1 = GPS Fix
            # 2 = DGPS
            # ------------------------------------------------

            try:

                fix_quality = int(
                    parts[6] or 0
                )

            except ValueError:

                fix_quality = 0

            # ------------------------------------------------
            # Fix Status
            # ------------------------------------------------

            self.fix = (
                fix_quality > 0
            )

            # ------------------------------------------------
            # Satelliten verwendet
            # ------------------------------------------------

            try:

                self.satellites_used = int(
                    parts[7] or 0
                )

            except ValueError:

                self.satellites_used = 0

            # ------------------------------------------------
            # HDOP
            # ------------------------------------------------

            try:

                self.hdop = float(
                    parts[8] or 99.99
                )

            except ValueError:

                self.hdop = 99.99

            # ------------------------------------------------
            # Position
            # ------------------------------------------------

            if latitude and longitude:

                self.latitude = (
                    self._nmea_to_decimal(
                        latitude,
                        latitude_direction
                    )
                )

                self.longitude = (
                    self._nmea_to_decimal(
                        longitude,
                        longitude_direction
                    )
                )

            # ------------------------------------------------
            # Status aktualisieren
            # ------------------------------------------------

            self._update_fix_text(
                fix_quality
            )

            # ------------------------------------------------
            # Dashboard informieren
            # ------------------------------------------------

            self._send_callback()

        except Exception as error:

            print(
                f"GGA Fehler: {error}",
                flush=True
            )

    # ========================================================
    # GSA
    # ========================================================

    def _parse_gsa(
        self,
        sentence
    ):

        try:

            parts = sentence.split(",")

            if len(parts) < 18:
                return

            # ------------------------------------------------
            # Fix Type
            #
            # 1 = kein Fix
            # 2 = 2D
            # 3 = 3D
            # ------------------------------------------------

            try:

                self.fix_type = int(
                    parts[2] or 1
                )

            except ValueError:

                self.fix_type = 0

            # ------------------------------------------------
            # Verwendete Satelliten zählen
            #
            # Felder 3 bis 14 enthalten
            # die PRNs der verwendeten Satelliten.
            # ------------------------------------------------

            satellite_count = 0

            for value in parts[3:15]:

                if value:

                    satellite_count += 1

            self.satellites_used = (
                satellite_count
            )

            # ------------------------------------------------
            # PDOP
            # ------------------------------------------------

            try:

                self.pdop = float(
                    parts[15] or 99.99
                )

            except ValueError:

                self.pdop = 99.99

            # ------------------------------------------------
            # HDOP
            # ------------------------------------------------

            try:

                self.hdop = float(
                    parts[16] or 99.99
                )

            except ValueError:

                self.hdop = 99.99

            # ------------------------------------------------
            # VDOP
            # ------------------------------------------------

            try:

                self.vdop = float(
                    parts[17].split("*")[0]
                    or 99.99
                )

            except ValueError:

                self.vdop = 99.99

            # ------------------------------------------------
            # Fix Text
            # ------------------------------------------------

            self._update_fix_text(
                self.fix_type
            )

        except Exception as error:

            print(
                f"GSA Fehler: {error}",
                flush=True
            )

    # ========================================================
    # GSV
    # ========================================================

    def _parse_gsv(
        self,
        sentence
    ):

        try:

            parts = sentence.split(",")

            if len(parts) < 4:
                return

            # ------------------------------------------------
            # Gesamtzahl Satelliten
            #
            # Beispiel:
            #
            # $GPGSV,3,1,11,...
            #
            # -> 11 sichtbare Satelliten
            # ------------------------------------------------

            try:

                self.satellites = int(
                    parts[3] or 0
                )

            except ValueError:

                self.satellites = 0

            # ------------------------------------------------
            # Satelliteninformationen
            #
            # Ein Satellit besteht aus:
            #
            # PRN
            # Elevation
            # Azimut
            # SNR
            # ------------------------------------------------

            satellite_data = []

            index = 4

            while index + 3 < len(parts):

                prn = parts[index]
                elevation = parts[index + 1]
                azimuth = parts[index + 2]
                snr = parts[index + 3]

                # Prüfen, ob das letzte Feld
                # einen NMEA Checksum-Teil enthält.

                if "*" in snr:

                    snr = snr.split("*")[0]

                if prn:

                    try:

                        prn_value = int(
                            prn
                        )

                    except ValueError:

                        prn_value = None

                else:

                    prn_value = None

                try:

                    elevation_value = (
                        float(elevation)
                        if elevation
                        else None
                    )

                except ValueError:

                    elevation_value = None

                try:

                    azimuth_value = (
                        float(azimuth)
                        if azimuth
                        else None
                    )

                except ValueError:

                    azimuth_value = None

                try:

                    snr_value = (
                        float(snr)
                        if snr
                        else None
                    )

                except ValueError:

                    snr_value = None

                satellite_data.append({
                    "prn": prn_value,
                    "elevation": elevation_value,
                    "azimuth": azimuth_value,
                    "snr": snr_value
                })

                index += 4

            # ------------------------------------------------
            # Informationen speichern
            # ------------------------------------------------

            if satellite_data:

                self.satellite_info = (
                    satellite_data
                )

        except Exception as error:

            print(
                f"GSV Fehler: {error}",
                flush=True
            )

    # ========================================================
    # RMC
    # ========================================================

    def _parse_rmc(
        self,
        sentence
    ):

        try:

            parts = sentence.split(",")

            if len(parts) < 9:
                return

            # ------------------------------------------------
            # UTC Zeit
            # ------------------------------------------------

            self.timestamp = parts[1]

            # ------------------------------------------------
            # Status
            #
            # A = gültig
            # V = ungültig
            # ------------------------------------------------

            status = parts[2]

            self.fix = (
                status == "A"
            )

            # ------------------------------------------------
            # Latitude
            # ------------------------------------------------

            latitude = parts[3]
            latitude_direction = parts[4]

            # ------------------------------------------------
            # Longitude
            # ------------------------------------------------

            longitude = parts[5]
            longitude_direction = parts[6]

            # ------------------------------------------------
            # Position
            # ------------------------------------------------

            if latitude and longitude:

                self.latitude = (
                    self._nmea_to_decimal(
                        latitude,
                        latitude_direction
                    )
                )

                self.longitude = (
                    self._nmea_to_decimal(
                        longitude,
                        longitude_direction
                    )
                )

            # ------------------------------------------------
            # Geschwindigkeit
            #
            # knots -> km/h
            # ------------------------------------------------

            try:

                speed_knots = float(
                    parts[7] or 0.0
                )

            except ValueError:

                speed_knots = 0.0

            self.speed = (
                speed_knots * 1.852
            )

            # ------------------------------------------------
            # GPS Kurs
            # ------------------------------------------------

            try:

                self.heading = float(
                    parts[8] or 0.0
                )

            except ValueError:

                self.heading = 0.0

            # ------------------------------------------------
            # Callback
            # ------------------------------------------------

            self._send_callback()

        except Exception as error:

            print(
                f"RMC Fehler: {error}",
                flush=True
            )

    # ========================================================
    # FIX STATUS
    # ========================================================

    def _update_fix_text(
        self,
        fix_type
    ):

        if fix_type == 3:

            self.fix_type_text = "3D FIX"
            self.fix = True

        elif fix_type == 2:

            self.fix_type_text = "2D FIX"
            self.fix = True

        elif fix_type == 1:

            self.fix_type_text = "KEIN FIX"
            self.fix = False

        else:

            self.fix_type_text = "KEIN FIX"
            self.fix = False

    # ========================================================
    # NMEA KOORDINATEN
    # ========================================================

    def _nmea_to_decimal(
        self,
        value,
        direction
    ):

        value = float(
            value
        )

        degrees = int(
            value / 100
        )

        minutes = (
            value
            - (degrees * 100)
        )

        decimal = (
            degrees
            + minutes / 60
        )

        if direction in (
            "S",
            "W"
        ):

            decimal *= -1

        return decimal

    # ========================================================
    # CALLBACK
    # ========================================================

    def _send_callback(self):

        if self.callback is None:
            return

        try:

            self.callback(
                self.latitude,
                self.longitude,
                self.speed,
                self.heading
            )

        except Exception as error:

            print(
                f"GPS Callback Fehler: {error}",
                flush=True
            )
